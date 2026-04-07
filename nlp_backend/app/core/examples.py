"""
Usage Examples & Test Cases
============================
Demonstrates the new linguistic grammar engine in action.
"""

from app.core.linguistic_grammar_engine import get_engine
from app.core.analyzer import GrammaticalAnalyzer
from app.core.rules import GrammarRules
from app.core.morphology import TeluguMorphology


def example_1_subject_verb_gender_mismatch():
    """
    Example 1: Subject-Verb Gender Mismatch
    
    Input: "ఆమె చేసాడు" (She did - WRONG: verb is masculine)
    Expected: "ఆమె చేసింది" (She did - verb is feminine)
    
    Error: Subject is feminine, verb is masculine
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Subject-Verb Gender Mismatch")
    print("="*70)
    
    tokens = ["ఆమె", "చేసాడు"]
    
    engine = get_engine()
    debug = engine.analyze_and_debug(tokens)
    
    print(f"\nInput tokens: {tokens}")
    print(f"Input sentence: {' '.join(tokens)}")
    
    print(f"\n--- Analysis ---")
    print(f"Subject: {debug['analysis']['subject']}")
    print(f"Verb:    {debug['analysis']['verb']}")
    
    print(f"\n--- Errors Detected ---")
    for error in debug['errors']:
        print(f"  Position {error.position}: {error.word}")
        print(f"  Type: {error.error_type}")
        print(f"  Explanation: {error.explanation}")
    
    print(f"\n--- Corrections Applied ---")
    for correction in debug['corrections']:
        print(f"  Position {correction['position']}: {correction['original']} → {correction['corrected']}")
    
    print(f"\nCorrected sentence: {' '.join(debug['corrected_tokens'])}")


def example_2_morphology_verb_stem_extraction():
    """
    Example 2: Verb Stem Extraction & Conjugation
    
    Shows how morphology module extracts stems and regenerates forms.
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Morphology - Verb Stem Extraction")
    print("="*70)
    
    # Extract stem from conjugated verb
    verbs = ["చేసాడు", "చేసింది", "చేసాను", "వెళ్ళాడు", "వెళ్ళింది"]
    
    print(f"\nExtracting stems from conjugated verbs:")
    for verb in verbs:
        stem = TeluguMorphology.get_verb_stem(verb)
        print(f"  {verb:12} → stem: {stem}")
    
    # Generate conjugations
    print(f"\n\nGenerating all conjugations for stem 'చేయ' in PAST tense:")
    from app.core.features import Person, Number, Gender, Tense
    
    conjugations = [
        (Person.THIRD, Number.SINGULAR, Gender.MASCULINE, "3rd masculine singular"),
        (Person.THIRD, Number.SINGULAR, Gender.FEMININE, "3rd feminine singular"),
        (Person.THIRD, Number.SINGULAR, Gender.NEUTER, "3rd neuter singular"),
        (Person.THIRD, Number.PLURAL, Gender.MASCULINE, "3rd plural"),
        (Person.FIRST, Number.SINGULAR, Gender.MASCULINE, "1st singular"),
        (Person.SECOND, Number.SINGULAR, Gender.MASCULINE, "2nd singular"),
    ]
    
    for person, number, gender, label in conjugations:
        form = TeluguMorphology.conjugate_verb(
            stem="చేయ",
            person=person,
            number=number,
            gender=gender,
            tense=Tense.PAST,
        )
        print(f"  {label:25} → {form}")


def example_3_postposition_missing():
    """
    Example 3: Missing Postposition
    
    Input: "నేను పాఠశాల వెళ్ళాను"
    Expected: "నేను పాఠశాలకు వెళ్ళాను"
    
    Directional verbs require dative case (కు) on objects.
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Missing Postposition (Dative Case)")
    print("="*70)
    
    tokens = ["నేను", "పాఠశాల", "వెళ్ళాను"]
    
    engine = get_engine()
    debug = engine.analyze_and_debug(tokens)
    
    print(f"\nInput tokens: {tokens}")
    print(f"Input sentence: {' '.join(tokens)}")
    
    print(f"\n--- Analysis ---")
    print(f"Subject: {debug['analysis']['subject']}")
    print(f"Verb:    {debug['analysis']['verb']}")
    if debug['analysis']['objects']:
        print(f"Objects: {debug['analysis']['objects']}")
    
    print(f"\n--- Errors Detected ---")
    for error in debug['errors']:
        print(f"  Position {error.position}: {error.word}")
        print(f"  Type: {error.error_type}")
        print(f"  Expected: {error.expected_form}")
        print(f"  Explanation: {error.explanation}")
    
    print(f"\n--- Corrections Applied ---")
    for correction in debug['corrections']:
        print(f"  Position {correction['position']}: {correction['original']} → {correction['corrected']}")
    
    print(f"\nCorrected sentence: {' '.join(debug['corrected_tokens'])}")


def example_4_analysis_only():
    """
    Example 4: Pure Analysis (No Correction)
    
    Shows what the analyzer discovers about any sentence.
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Pure Grammatical Analysis")
    print("="*70)
    
    test_sentences = [
        ["నేను", "చేసాను"],
        ["అతను", "చేసాడు"],
        ["ఆమె", "చేసింది"],
        ["మీరు", "చేసారు"],
    ]
    
    analyzer = GrammaticalAnalyzer()
    
    for tokens in test_sentences:
        print(f"\nAnalyzing: {' '.join(tokens)}")
        analysis = analyzer.analyze(tokens)
        
        if analysis.subject:
            print(f"  Subject: {analysis.subject.word} ({analysis.subject.gender.value}, {analysis.subject.person.name} person)")
        
        if analysis.verb:
            print(f"  Verb:    {analysis.verb.word} (stem: {analysis.verb.stem}, {analysis.verb.tense.value})")
        
        # Check agreement
        if analysis.subject and analysis.verb:
            person_match = analysis.subject.person == analysis.verb.person
            gender_match = analysis.subject.gender == analysis.verb.gender
            print(f"  Agreement: person={person_match}, gender={gender_match}")


def example_5_complex_sentence():
    """
    Example 5: More Complex Sentence
    
    Shows handling of full sentence with multiple elements.
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Complex Sentence Analysis")
    print("="*70)
    
    # అతని సోదరుడు చిన్న ఇంటికి వెళ్ళాడు
    # His brother went to a small house
    tokens = ["అతను", "చిన్నది", "ఇంటికి", "వెళ్ళాడు"]
    
    engine = get_engine()
    debug = engine.analyze_and_debug(tokens)
    
    print(f"\nInput: {' '.join(tokens)}")
    print(f"(His brother went to a small house - SLIGHTLY SIMPLIFIED)")
    
    print(f"\n--- Extracted Features ---")
    if debug['analysis']['subject']:
        s = debug['analysis']['subject']
        print(f"Subject: {s.word}")
        print(f"  Person: {s.person.name}")
        print(f"  Number: {s.number.value}")
        print(f"  Gender: {s.gender.value}")
    
    if debug['analysis']['verb']:
        v = debug['analysis']['verb']
        print(f"Verb: {v.word}")
        print(f"  Stem: {v.stem}")
        print(f"  Person: {v.person.name}")
        print(f"  Tense: {v.tense.value}")
        print(f"  Gender: {v.gender.value}")
    
    if debug['analysis']['objects']:
        print(f"Objects: {len(debug['analysis']['objects'])} found")
        for obj in debug['analysis']['objects']:
            print(f"  - {obj.word} (position {obj.position})")
    
    print(f"\n--- Validation Results ---")
    if debug['errors']:
        print(f"Errors found: {len(debug['errors'])}")
        for error in debug['errors']:
            print(f"  - {error.error_type}")
    else:
        print("No errors found!")
    
    if debug['corrections']:
        print(f"\nCorrections applied: {len(debug['corrections'])}")
        for corr in debug['corrections']:
            print(f"  - {corr['original']} → {corr['corrected']}")
    else:
        print("\nNo corrections needed.")


def run_all_examples():
    """Run all examples."""
    try:
        example_1_subject_verb_gender_mismatch()
    except Exception as e:
        print(f"Example 1 error: {e}")
    
    try:
        example_2_morphology_verb_stem_extraction()
    except Exception as e:
        print(f"Example 2 error: {e}")
    
    try:
        example_3_postposition_missing()
    except Exception as e:
        print(f"Example 3 error: {e}")
    
    try:
        example_4_analysis_only()
    except Exception as e:
        print(f"Example 4 error: {e}")
    
    try:
        example_5_complex_sentence()
    except Exception as e:
        print(f"Example 5 error: {e}")
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)


if __name__ == "__main__":
    run_all_examples()
