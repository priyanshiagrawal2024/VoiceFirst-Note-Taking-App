import re
from typing import Dict, Any, List, Optional, Tuple

class AutoSpeechCorrectionService:
    """
    Intelligent speech-to-text auto-correction engine for college students.
    Corrects common acoustic mishearings, phonetic typos, and academic terminology
    across Physics, Chemistry, Biology, Computer Science, Mathematics, and History,
    as well as Voice-First navigation and study commands.
    """

    # Comprehensive phonetic and acoustic substitution dictionary
    # Maps regex pattern -> canonical corrected term
    PHONETIC_CORRECTIONS = [
        # --- Voice-First Navigation & Study Commands ---
        (r"\b(?:quize|quizz|quizs|quizes)\s+me\b", "quiz me"),
        (r"\b(?:take\s+a\s+quize|give\s+me\s+a\s+quize|start\s+quize)\b", "start quiz"),
        (r"\b(?:flshcard|flash\s+card|flash\s+cards|flsh\s+cards)\b", "flashcards"),
        (r"\b(?:repete|repiat|re-peat)\b", "repeat"),
        (r"\b(?:nex|nekt|nxt)\b", "next"),
        (r"\b(?:flipp|fleep|lip|turn\s+over)\b", "flip"),
        (r"\b(?:previus|privious|preveous)\b", "previous"),
        (r"\b(?:inturrupt|intrupt|interupt)\b", "stop"),
        (r"\b(?:start\s+lectur|begin\s+lectur)\b", "start lecture"),
        (r"\b(?:end\s+lectur|finish\s+lectur)\b", "end lecture"),
        (r"\b(?:cread\s+note|creat\s+note|make\s+a\s+not)\b", "note:"),
        (r"\b(?:revise\s+(?:my\s+)?)?weak\s+topics?\b", "revise my weak topics"),
        (r"\b(?:open|show|go\s+to|view)\s+(?:the\s+)?(?:recents|recent\s+notes?|latest\s+notes?)\b", "open recents"),
        (r"^(?:please\s+)?(?:read\s+)?(?:recents|recent\s+notes?|latest\s+notes?)\b", "read recent notes"),
        (r"\b(?:delet|delit|erace|remov)\s+(?:last\s+)?note\b", "delete last note"),
        (r"\b(?:serch|searche|surch)\b", "search"),
        (r"\b(?:fine|fined)\s+(?:my\s+)?notes\b", "find notes"),

        # --- College Subjects ---
        (r"\b(?:camistry|chemestry|kemistry|chemitry)\b", "Chemistry"),
        (r"\b(?:fiziks|fizix|physic|physix)\b", "Physics"),
        (r"\b(?:bayology|biologie|bioligy)\b", "Biology"),
        (r"\b(?:cumputer\s+science|comp\s+sci|computer\s+sci)\b", "Computer Science"),
        (r"\b(?:geogrophy|geograpy|geografy)\b", "Geography"),
        (r"\b(?:calcolus|calclus|calculas)\b", "Calculus"),
        (r"\b(?:algoritms|algorithems|algo\s+rithm)\b", "algorithms"),

        # --- Voice Command Phonetic Repairs ---
        (r"\b(?:sir|star|set)\s+(geography|biology|physics|chemistry|computer\s+science|mathematics|history)\s+notes?\b", r"start \1 notes"),
        (r"\b(?:sir|star|set)\s+(geography|biology|physics|chemistry|computer\s+science|mathematics|history)\s+lecture\b", r"start \1 lecture"),

        # --- Geography ---
        (r"\b(?:plate\s+tektonics|plate\s+tektonik)\b", "plate tectonics"),
        (r"\b(?:litho\s+sphere|lithosfear)\b", "lithosphere"),
        (r"\b(?:continantal\s+drift|continental\s+drif)\b", "continental drift"),
        (r"\b(?:whethering|wethering)\b", "weathering"),
        (r"\b(?:endogenic|endo\s+genic)\b", "endogenic"),
        (r"\b(?:exogenic|exo\s+genic)\b", "exogenic"),
        (r"\b(?:ekwayter|ekwater)\b", "equator"),
        (r"\b(?:prime\s+maridian|prime\s+meridien)\b", "prime meridian"),
        (r"\b(?:tropo\s+sphere|troposfear)\b", "troposphere"),
        (r"\b(?:strato\s+sphere|stratosfear)\b", "stratosphere"),

        # --- Biology & Life Sciences ---
        (r"\b(?:my\s+toes\s+is|my\s+tosis|mito\s+sis)\b", "mitosis"),
        (r"\b(?:my\s+oh\s+sis|meo\s+sis|mayo\s+sis)\b", "meiosis"),
        (r"\b(?:sell\s+division)\b", "cell division"),
        (r"\b(?:power\s+house\s+of\s+sell|powerhouse\s+of\s+sell|powerhouse\s+of\s+the\s+sell)\b", "powerhouse of the cell"),
        (r"\b(?:photo\s+synthesis|photosinthesis|fotosinthesis)\b", "photosynthesis"),
        (r"\b(?:ribo\s+some|ribo\s+somes)\b", "ribosomes"),
        (r"\b(?:celluler\s+respiration|cellular\s+resperation)\b", "cellular respiration"),
        (r"\b(?:dee\s+en\s+ay|d\s+n\s+a)\b", "DNA"),
        (r"\b(?:are\s+en\s+ay|r\s+n\s+a)\b", "RNA"),
        (r"\b(?:osmoses|osmosiss)\b", "osmosis"),
        (r"\b(?:cyto\s+plasm|cytoplasim)\b", "cytoplasm"),
        (r"\b(?:chromo\s+some|chromosom)\b", "chromosome"),
        (r"\b(?:chloro\s+plast|chloroplaste)\b", "chloroplast"),

        # --- Chemistry ---
        (r"\b(?:boyle\s+slaw|boyles\s+law|boils\s+law)\b", "Boyle's law"),
        (r"\b(?:charles\s+law|charleses\s+law)\b", "Charles's law"),
        (r"\b(?:avagadro|avagadro's|avogadros)\b", "Avogadro's"),
        (r"\b(?:covalent\s+bond|kovalent\s+bond)\b", "covalent bond"),
        (r"\b(?:ionic\s+bond|ionik\s+bond)\b", "ionic bond"),
        (r"\b(?:periodic\s+tabel|periodik\s+table)\b", "periodic table"),
        (r"\b(?:acid\s+and\s+base|acids\s+and\s+base)\b", "acids and bases"),
        (r"\b(?:electronegativity|electro\s+negativity)\b", "electronegativity"),
        (r"\b(?:endothermic|endo\s+thermic)\b", "endothermic"),
        (r"\b(?:exothermic|exo\s+thermic)\b", "exothermic"),
        (r"\b(?:stoychiometry|stoechiometry|stoichiometrie)\b", "stoichiometry"),
        (r"\b(?:titration|titrations)\b", "titration"),
        (r"\b(?:valence\s+electron|valens\s+electron)\b", "valence electron"),
        (r"\b(?:catalist|catalists)\b", "catalyst"),

        # --- Physics ---
        (r"\b(?:new\s+ton|new\s+tons|newtons)\b", "Newton's"),
        (r"\b(?:newton's\s+low|newton\s+law)\b", "Newton's law"),
        (r"\b(?:thermo\s+dynamic|thermo\s+dynamics|thermal\s+dynamics)\b", "thermodynamics"),
        (r"\b(?:kinetik\s+energy|kinetic\s+enery)\b", "kinetic energy"),
        (r"\b(?:potential\s+enery)\b", "potential energy"),
        (r"\b(?:gravitational\s+forse|gravity\s+forse)\b", "gravitational force"),
        (r"\b(?:quantum\s+mechanix|quantum\s+mecanics)\b", "quantum mechanics"),
        (r"\b(?:centripetal\s+forse)\b", "centripetal force"),
        (r"\b(?:aceleration|accelleration)\b", "acceleration"),
        (r"\b(?:coulombs\s+law|coulomb\s+law)\b", "Coulomb's law"),
        (r"\b(?:ohms\s+law|ohm\s+law)\b", "Ohm's law"),
        (r"\b(?:velocity|velosity)\b", "velocity"),
        (r"\b(?:electromagnetism|electro\s+magnetism)\b", "electromagnetism"),

        # --- Computer Science ---
        (r"\b(?:pythun|pie\s+thon|pie\s+ton)\b", "Python"),
        (r"\b(?:recusion|re-cursion|recurshun)\b", "recursion"),
        (r"\b(?:algo\s+rithm|algorythm|algoritm)\b", "algorithm"),
        (r"\b(?:big\s+o\s+notation|big\s+oh|big\s+o)\b", "Big O notation"),
        (r"\b(?:polymorphism|poly\s+morphism)\b", "polymorphism"),
        (r"\b(?:inheritance|inheretance)\b", "inheritance"),
        (r"\b(?:data\s+structure|data\s+structures)\b", "data structures"),
        (r"\b(?:hash\s+map|hashmap|hash\s+table)\b", "hash map"),
        (r"\b(?:binary\s+tree|binery\s+tree)\b", "binary tree"),
        (r"\b(?:linked\s+list|link\s+list)\b", "linked list"),
        (r"\b(?:sql|sequel|s\s+q\s+l)\b", "SQL"),
        (r"\b(?:data\s+base|datebase)\b", "database"),
        (r"\b(?:byte\s+code|bytecode)\b", "bytecode"),
        (r"\b(?:concurrency|concurancy)\b", "concurrency"),
        (r"\b(?:quicksort|quick\s+sort)\b", "quicksort"),
        (r"\b(?:mergesort|merge\s+sort)\b", "mergesort"),

        # --- Mathematics ---
        (r"\b(?:derivitive|derivatives|derivitaves)\b", "derivative"),
        (r"\b(?:integrel|integrals|integrels)\b", "integral"),
        (r"\b(?:pythagorean\s+theorem|pythagoras\s+theorem)\b", "Pythagorean theorem"),
        (r"\b(?:eigen\s+value|eigen\s+values)\b", "eigenvalue"),
        (r"\b(?:probability|probibility)\b", "probability"),
        (r"\b(?:normal\s+distrebution|normal\s+distribution)\b", "normal distribution"),
        (r"\b(?:matrix\s+multiplication|matrex\s+multiplication)\b", "matrix multiplication"),

        # --- History & Social Studies ---
        (r"\b(?:world\s+war\s+one|world\s+war\s+1|ww\s+one|ww1)\b", "World War I"),
        (r"\b(?:world\s+war\s+two|world\s+war\s+2|ww\s+two|ww2)\b", "World War II"),
        (r"\b(?:industrial\s+revolution|industriel\s+revolution)\b", "Industrial Revolution"),
        (r"\b(?:treaty\s+of\s+versailles|treaty\s+of\s+versaille)\b", "Treaty of Versailles"),
    ]

    # Domain indicators for auto-detecting academic subject
    DOMAIN_KEYWORDS = {
        "Chemistry": [
            "boyle", "charles", "avogadro", "covalent", "ionic", "periodic table",
            "acid", "base", "ph scale", "electronegativity", "endothermic", "exothermic",
            "stoichiometry", "titration", "atom", "molecule", "reaction", "solution", "molarity"
        ],
        "Physics": [
            "newton", "gravity", "acceleration", "force", "velocity", "inertia", "momentum",
            "thermodynamics", "kinetic energy", "potential energy", "quantum", "coulomb",
            "ohm's law", "electromagnetism", "centripetal", "optics", "wavelength", "frequency"
        ],
        "Computer Science": [
            "python", "algorithm", "recursion", "data structure", "binary tree", "binary search",
            "linked list", "hash map", "big o", "time complexity", "complexity", "search",
            "polymorphism", "inheritance", "sql", "database", "stack", "queue", "graph",
            "sorting", "quicksort", "concurrency", "operating system"
        ],
        "Mathematics": [
            "calculus", "derivative", "integral", "pythagorean", "eigenvalue", "matrix",
            "probability", "distribution", "theorem", "logarithm", "trigonometry", "algebra"
        ],
        "Biology": [
            "mitosis", "meiosis", "cell division", "dna", "rna", "photosynthesis", "mitochondria",
            "ribosome", "chloroplast", "cellular respiration", "osmosis", "chromosome", "genetics",
            "evolution", "organism", "enzyme"
        ],
        "History": [
            "world war", "treaty of versailles", "industrial revolution", "renaissance",
            "civil war", "revolution", "constitution", "empire", "cold war", "democracy"
        ],
        "Geography": [
            "geography", "plate tectonics", "lithosphere", "atmosphere", "equator",
            "meridian", "latitude", "longitude", "erosion", "topography", "glacier",
            "climate", "biome", "tectonic", "continental drift", "volcano", "earthquake", "tundra",
            "weathering", "landform", "endogenic", "exogenic", "earth interior", "crust", "mantle", "core"
        ],
    }

    @classmethod
    def correct_transcript(cls, text: str, gemini_service=None, context: Optional[Dict[str, Any]] = None) -> Tuple[str, List[str]]:
        """
        Applies fast phonetic auto-corrections first, followed by Gemini if available.
        Returns: (corrected_text, list_of_corrections_made)
        """
        if not text:
            return "", []

        cleaned = text.strip()
        corrections_made = []

        # 1. Apply phonetic dictionary replacements
        for pattern_str, replacement in cls.PHONETIC_CORRECTIONS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(cleaned)
            if match:
                original_match = match.group(0)
                if original_match != replacement:
                    cleaned = pattern.sub(replacement, cleaned)
                    corrections_made.append(f"'{original_match}' -> '{replacement}'")

        # 2. Check Gemini for advanced contextual correction if available
        if gemini_service and gemini_service.is_available():
            try:
                gemini_corrected = gemini_service.auto_correct_speech(cleaned, context=context)
                if gemini_corrected and len(gemini_corrected.strip()) > 0:
                    cleaned = gemini_corrected.strip()
            except Exception as e:
                # Local corrections are safe and reliable
                pass

        return cleaned, corrections_made

    @classmethod
    def detect_subject(cls, text: str, fallback_subject: str = "General") -> str:
        """
        Auto-detects the academic subject domain from the text content.
        """
        if not text:
            return fallback_subject

        text_lower = text.lower()

        # Check explicit subject mentions: e.g. "geography is...", "in chemistry", "for physics", "biology lecture"
        for subject in ["Chemistry", "Physics", "Computer Science", "Mathematics", "Biology", "History", "Geography"]:
            subj_lower = subject.lower()
            if (f"in {subj_lower}" in text_lower or 
                f"for {subj_lower}" in text_lower or 
                f"about {subj_lower}" in text_lower or
                f"{subj_lower} is" in text_lower or
                text_lower.startswith(subj_lower)):
                return subject

        # Check domain keywords and choose best fit
        best_subj = fallback_subject
        max_matches = 0
        for subject, keywords in cls.DOMAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > max_matches:
                max_matches = matches
                best_subj = subject

        return best_subj if max_matches > 0 else fallback_subject
