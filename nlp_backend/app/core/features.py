"""
Grammatical Features for Telugu
================================
Structured representation of grammatical properties.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class Person(Enum):
    """Grammatical person: 1st, 2nd, 3rd."""
    FIRST = 1    # నేను (I)
    SECOND = 2   # నీవు (you)
    THIRD = 3    # అతను, ఆమె, ఇది (he, she, it)


class Number(Enum):
    """Grammatical number: singular or plural."""
    SINGULAR = "singular"
    PLURAL = "plural"


class Gender(Enum):
    """Grammatical gender: masculine, feminine, neuter."""
    MASCULINE = "masculine"    # అతను, అతడు
    FEMININE = "feminine"      # ఆమె, ఆమె
    NEUTER = "neuter"          # ఇది, అది


class Tense(Enum):
    """Grammatical tense."""
    PAST = "past"              # చేసాడు
    PRESENT = "present"        # చేస్తున్నాడు
    FUTURE = "future"          # చేయాడు
    HABITUAL = "habitual"      # చేస్తాడు
    PERFECT = "perfect"        # చేసుకున్నాడు


class Mood(Enum):
    """Grammatical mood: indicative, conditional, imperative."""
    INDICATIVE = "indicative"
    CONDITIONAL = "conditional"
    IMPERATIVE = "imperative"
    SUBJUNCTIVE = "subjunctive"


class GrammaticalRole(Enum):
    """Role of word in sentence."""
    SUBJECT = "subject"
    VERB = "verb"
    OBJECT = "object"
    POSTPOSITION = "postposition"
    NOUN = "noun"
    ADJECTIVE = "adjective"
    UNKNOWN = "unknown"


@dataclass
class SubjectFeatures:
    """Grammatical features of a subject."""
    person: Person
    number: Number
    gender: Gender
    word: str
    position: int
    
    def __repr__(self) -> str:
        return (f"Subject({self.word}, "
                f"P{self.person.value} "
                f"{self.number.value} "
                f"{self.gender.value})")


@dataclass
class VerbFeatures:
    """Grammatical features of a verb."""
    person: Person
    number: Number
    gender: Gender
    tense: Tense
    mood: Mood
    stem: str           # Base form without conjugation
    word: str          # Full conjugated form
    position: int
    
    def __repr__(self) -> str:
        return (f"Verb({self.word}, "
                f"P{self.person.value} "
                f"{self.number.value} "
                f"{self.gender.value} "
                f"{self.tense.value})")


@dataclass
class NounFeatures:
    """Grammatical features of a noun."""
    person: Person      # Person: 3rd for nouns
    number: Number
    gender: Optional[Gender]  # May be implicit
    case: Optional[str]       # Nominative, accusative, dative, etc.
    word: str
    position: int
    
    def __repr__(self) -> str:
        return (f"Noun({self.word}, "
                f"{self.number.value} "
                f"{self.gender or 'no-gender'})")


@dataclass
class GrammaticalAnalysis:
    """Complete grammatical analysis of a sentence."""
    tokens: list  # Original tokens
    subject: Optional[SubjectFeatures] = None
    verb: Optional[VerbFeatures] = None
    objects: list = None  # List of NounFeatures
    
    def __post_init__(self):
        if self.objects is None:
            self.objects = []


# ─── Subject Type Detection ─────────────────────────────────────────────

PRONOUN_FEATURES = {
    # First person
    "నేను": SubjectFeatures(Person.FIRST, Number.SINGULAR, Gender.MASCULINE, "నేను", 0),
    "మనం": SubjectFeatures(Person.FIRST, Number.PLURAL, Gender.MASCULINE, "మనం", 0),
    "మేము": SubjectFeatures(Person.FIRST, Number.PLURAL, Gender.MASCULINE, "మేము", 0),
    
    # Second person
    "నీవు": SubjectFeatures(Person.SECOND, Number.SINGULAR, Gender.MASCULINE, "నీవు", 0),
    "మీరు": SubjectFeatures(Person.SECOND, Number.PLURAL, Gender.MASCULINE, "మీరు", 0),
    
    # Third person masculine
    "అతను": SubjectFeatures(Person.THIRD, Number.SINGULAR, Gender.MASCULINE, "అతను", 0),
    "అతడు": SubjectFeatures(Person.THIRD, Number.SINGULAR, Gender.MASCULINE, "అతడు", 0),
    "వారు": SubjectFeatures(Person.THIRD, Number.PLURAL, Gender.MASCULINE, "వారు", 0),
    "వాళ్లు": SubjectFeatures(Person.THIRD, Number.PLURAL, Gender.MASCULINE, "వాళ్లు", 0),
    
    # Third person feminine
    "ఆమె": SubjectFeatures(Person.THIRD, Number.SINGULAR, Gender.FEMININE, "ఆమె", 0),
    "ఆమెలు": SubjectFeatures(Person.THIRD, Number.PLURAL, Gender.FEMININE, "ఆమెలు", 0),
    
    # Third person neuter
    "ఇది": SubjectFeatures(Person.THIRD, Number.SINGULAR, Gender.NEUTER, "ఇది", 0),
    "అది": SubjectFeatures(Person.THIRD, Number.SINGULAR, Gender.NEUTER, "అది", 0),
    "అవి": SubjectFeatures(Person.THIRD, Number.PLURAL, Gender.NEUTER, "అవి", 0),
}
