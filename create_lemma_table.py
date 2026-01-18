# This script processes a Finnish word frequency list and generates a lemma table
# using both Voikko and spaCy analyzers with proper POS tag mapping.

import csv
import os
from pathlib import Path
import argparse
import re

try:
    from libvoikko import Voikko
    library_dir = Path('/opt/homebrew/opt/libvoikko/lib')
    Voikko.setLibrarySearchPath(str(library_dir))
except ImportError:
    print("Error: The 'libvoikko' library is not installed.")
    print("Please install it using: pip install libvoikko")
    exit(1)

try:
    import spacy
except ImportError:
    print("Error: The 'spacy' library is not installed.")
    print("Please install it using: pip install spacy")
    exit(1)


def map_voikko_pos(analysis):
    """
    Maps Voikko CLASS and SIJAMUOTO to the target POS tag set.
    
    Args:
        analysis: A single analysis dictionary from Voikko
        
    Returns:
        A POS tag string or None if it doesn't match our tag set
    """
    v_class = analysis.get('CLASS', '')
    v_sijamuoto = analysis.get('SIJAMUOTO', '')
    
    # NOUN: 'nimisana'
    if v_class == 'nimisana':
        return 'NOUN'
    
    # PROPN: proper names (etunimi, sukunimi, paikannimi)
    if v_class in ['etunimi', 'sukunimi', 'paikannimi']:
        return 'PROPN'
    
    # VERB: 'teonsana'
    if v_class == 'teonsana':
        return 'VERB'
    if v_class == 'kieltosana':
        return 'VERB'
    
    # ADJ: laatusana or nimisana_laatusana with standard noun cases
    if v_class in ['laatusana', 'nimisana_laatusana']:
        standard_cases = {'nimento', 'osanto', 'sisaolento', 'omanto', 
                         'ulkoolento', 'sisaantulento'}
        if v_sijamuoto in standard_cases:
            return 'ADJ'
    
    # ADV: seikkasana OR laatusana with kerrontosti/-sti OR keinonto (instructive)
    if v_class == 'seikkasana':
        return 'ADV'
    if v_class in ['laatusana', 'nimisana_laatusana']:
        if v_sijamuoto in ['kerrontosti', 'keinonto']:
            return 'ADV'
    
    # PRON: 'asemosana'
    if v_class == 'asemosana':
        return 'PRON'
    
    # NUM: 'lukusana'
    if v_class == 'lukusana':
        return 'NUM'
    
    # ADP: 'suhdesana'
    if v_class == 'suhdesana':
        return 'ADP'
    
    # CONJ: 'sidesana' (maps to both CCONJ and SCONJ)
    if v_class == 'sidesana':
        return 'CONJ'
    
    # OTHER: huudahdussana, etc.
    if v_class in ['huudahdussana']:
        return 'OTHER'
    
    return None


def map_spacy_pos(spacy_pos):
    """
    Maps spaCy Universal POS tags to the target tag set.
    
    Args:
        spacy_pos: Universal Dependencies POS tag from spaCy
        
    Returns:
        A POS tag string or None if not in our tag set
    """
    if spacy_pos == 'AUX':
        return 'VERB'
    # Direct mappings
    valid_tags = {'NOUN', 'PROPN', 'VERB', 'ADJ', 'ADV', 'PRON', 'NUM', 'ADP'}
    if spacy_pos in valid_tags:
        return spacy_pos
    
    # CONJ: combine CCONJ and SCONJ
    if spacy_pos in ['CCONJ', 'SCONJ']:
        return 'CONJ'
    
    # OTHER: INTJ, PUNCT, SYM, X
    if spacy_pos in ['INTJ', 'PUNCT', 'SYM', 'X']:
        return 'OTHER'
    
    return None


def analyze_with_voikko(voikko, surface_form):
    """
    Analyze a word with Voikko and return (pos, lemma, source) tuples.
    
    Args:
        voikko: Initialized Voikko instance
        surface_form: The word to analyze
        
    Returns:
        List of (pos, lemma, 'voikko') tuples
    """
    results = []
    analyses = voikko.analyze(surface_form)
    
    for analysis in analyses:
        # Check if this is a participle first
        participle = analysis.get('PARTICIPLE', '')
        
        # If it's a past participle (past_active, past_passive) or agent participle (present_active, present_passive),
        # treat it as a VERB and use WORDBASES for the verbal lemma
        if participle in ['past_active', 'past_passive', 'present_active', 'present_passive', 'agent']:
            wordbases = analysis.get('WORDBASES', '')
            if wordbases:
                # Extract the verbal base from WORDBASES
                # Format is typically: "+base(lemma)+suffix(+suffix)"
                match = re.search(r'\+\w+\(([^)]+)\)', wordbases)
                if match:
                    verbal_lemma = match.group(1)
                    results.append(('VERB', verbal_lemma, 'voikko'))
                    continue
        
        # If it's a negative participle (-maton/-mätön forms like "tekemätön"),
        # treat it as ADJ but use the verbal lemma from WORDBASES
        if participle == 'negation':
            wordbases = analysis.get('WORDBASES', '')
            if wordbases:
                # Extract the verbal base from WORDBASES
                # Format is typically: "+teke(tehdä)+mä(+ä)+tön(+tön)"
                match = re.search(r'\+\w+\(([^)]+)\)', wordbases)
                if match:
                    verbal_lemma = match.group(1)
                    results.append(('ADJ', verbal_lemma, 'voikko'))
                    continue
        
        # Otherwise, use the standard POS mapping
        pos = map_voikko_pos(analysis)
        if pos:
            lemma = analysis.get('BASEFORM', surface_form)
            results.append((pos, lemma, 'voikko'))
    
    return results


def analyze_with_spacy(nlp, surface_form):
    """
    Analyze a word with spaCy and return (pos, lemma, source) tuples.
    
    Args:
        nlp: Initialized spaCy model
        surface_form: The word to analyze
        
    Returns:
        List of (pos, lemma, 'spacy') tuples
    """
    results = []
    doc = nlp(surface_form)
    
    for token in doc:
        pos = map_spacy_pos(token.pos_)
        if pos:
            lemma = token.lemma_
            results.append((pos, lemma, 'spacy'))
    
    return results


def resolve_lemmas(voikko, nlp, surface_form):
    """
    Resolve lemmas for a surface form, prioritizing Voikko over spaCy.
    
    Args:
        voikko: Initialized Voikko instance
        nlp: Initialized spaCy model
        surface_form: The word to analyze
        
    Returns:
        List of unique (pos, lemma, source) tuples
    """
    # Try Voikko first
    results = analyze_with_voikko(voikko, surface_form)
    
    # If Voikko returns nothing, try spaCy
    if not results:
        results = analyze_with_spacy(nlp, surface_form)
    
    # Deduplicate on (pos, lemma) while preserving order and source
    seen = set()
    unique_results = []
    for pos, lemma, source in results:
        key = (pos, lemma)
        if key not in seen:
            seen.add(key)
            unique_results.append((pos, lemma, source))
    
    return unique_results


def load_frequency_words(filepath, limit=None):
    """
    Load surface forms from frequency word file.
    
    Args:
        filepath: Path to the frequency word file (format: "word count")
        limit: Optional limit on the number of words to process
        
    Returns:
        List of unique surface forms in processing order
    """
    surface_forms = []
    seen = set()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            # Extract only the word token (first part), ignore the frequency count
            word = parts[0]
            if word and word not in seen:
                surface_forms.append(word)
                seen.add(word)
                if limit is not None and len(surface_forms) >= limit:
                    break
    
    return surface_forms


def main():
    """
    Main processing pipeline.
    """
    parser = argparse.ArgumentParser(description="Generate lemma table from Finnish frequency list.")
    parser.add_argument("--limit", type=int, default=None, help="Process at most this many unique surface forms.")
    args = parser.parse_args()
    
    # Paths
    input_file = Path("freqwords/fi_100k.txt")
    output_dir = Path("output")
    # If a limit was provided, include it in the output filename; otherwise use the full-collection name
    if args.limit is not None:
        output_file = output_dir / f"fi_{args.limit}_lemmas.csv"
    else:
        output_file = output_dir / "fi_100k_lemmas.csv"
    
    # Load surface forms
    print(f"Loading frequency words from {input_file}...")
    surface_forms = load_frequency_words(input_file, limit=args.limit)
    print(f"Loaded {len(surface_forms)} unique surface forms.")
    
    # Initialize analyzers
    print("\nInitializing Voikko for Finnish...")
    try:
        voikko = Voikko("fi")
    except Exception as e:
        print(f"Failed to initialize Voikko: {e}")
        return
    
    print("Loading spaCy Finnish model...")
    try:
        # Try loading normally first
        nlp = spacy.load("fi_core_news_md")
    except OSError:
        # Try loading from an alternative path
        model_path = "/Users/harrycslau/miniconda3/envs/lingoappenv/lib/python3.11/site-packages/fi_core_news_lg/fi_core_news_lg-3.8.0"
        if Path(model_path).exists():
            print(f"Loading from alternative path: {model_path}")
            nlp = spacy.load(model_path)
        else:
            print("Error: Finnish spaCy model not found.")
            print("Please install it using: python -m spacy download fi_core_news_md")
            print(f"Or set the correct path in the script (currently: {model_path})")
            voikko.terminate()
            return
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Process words and write to CSV
    print(f"\nProcessing words and writing to {output_file}...")
    unanalyzable = []
    total_rows = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['surface_form', 'pos', 'lemma'])
        
        for surface_form in surface_forms:
            results = resolve_lemmas(voikko, nlp, surface_form)
            
            if results:
                for pos, lemma, source in results:
                    # Write only surface_form, pos, lemma (drop source)
                    writer.writerow([surface_form, pos, lemma])
                    total_rows += 1
            else:
                unanalyzable.append(surface_form)
    
    # Summary
    print(f"\n✅ Processing complete!")
    print(f"   Total rows written: {total_rows}")
    print(f"   Output file: {output_file}")
    
    if unanalyzable:
        print(f"\n⚠️  {len(unanalyzable)} token(s) could not be analyzed:")
        for word in unanalyzable:
            print(f"   - {word}")
    
    # Cleanup
    voikko.terminate()


if __name__ == "__main__":
    main()

