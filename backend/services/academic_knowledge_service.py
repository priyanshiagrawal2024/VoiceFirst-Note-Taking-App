import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import get_db_connection
from services.note_service import NoteService

class AcademicKnowledgeService:
    """
    Comprehensive multi-domain academic curriculum and dynamic material generator.
    Enables instant note generation, quiz generation, and flashcard creation
    across Chemistry, Physics, Computer Science, Mathematics, History, and Biology.
    Automatically stores generated study materials into SQLite for student persistence.
    """

    CURRICULUM = {
        "Chemistry": {
            "notes": [
                {
                    "text": "Boyle's law states that the pressure of a given mass of gas is inversely proportional to its volume at constant temperature.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, squeezing a sealed syringe reduces gas volume and sharply increases the pressure inside.",
                    "tag": "Example"
                },
                {
                    "text": "A covalent bond is a chemical bond formed by the sharing of electron pairs between nonmetal atoms.",
                    "tag": "Definition"
                },
                {
                    "text": "Important exam point: Electronegativity increases across a period from left to right and decreases down a group.",
                    "tag": "Important"
                },
                {
                    "text": "Acids are proton donors that produce hydrogen ions in aqueous solution, resulting in a pH value less than seven.",
                    "tag": "Definition"
                },
                {
                    "text": "Charles's law states that volume is directly proportional to absolute temperature when pressure remains constant.",
                    "tag": "Definition"
                },
                {
                    "text": "Exothermic reactions release thermal energy to the surroundings, resulting in a negative enthalpy change.",
                    "tag": "Important"
                },
                {
                    "text": "For example, hydrochloric acid reacting with sodium hydroxide forms sodium chloride salt and water in neutralization.",
                    "tag": "Example"
                }
            ],
            "quiz": [
                {
                    "question": "What does Boyle's law state regarding ideal gases?",
                    "options": [
                        "Pressure and volume are inversely proportional at constant temperature.",
                        "Volume is directly proportional to temperature at constant pressure.",
                        "Pressure is directly proportional to temperature.",
                        "Mass is converted to energy in chemical reactions."
                    ],
                    "correct_answer": "A",
                    "expected_answer": "Pressure and volume are inversely proportional at constant temperature."
                },
                {
                    "question": "What type of chemical bond is formed by the sharing of electron pairs?",
                    "options": [
                        "Ionic bond",
                        "Covalent bond",
                        "Hydrogen bond",
                        "Metallic bond"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "A covalent bond involves shared electron pairs between atoms."
                },
                {
                    "question": "How does electronegativity change across a period from left to right in the periodic table?",
                    "options": [
                        "It decreases steadily.",
                        "It remains completely constant.",
                        "It increases across the period.",
                        "It drops to zero."
                    ],
                    "correct_answer": "C",
                    "expected_answer": "Electronegativity increases across a period from left to right."
                },
                {
                    "question": "What is the defining characteristic of an acidic aqueous solution?",
                    "options": [
                        "pH greater than 7",
                        "Proton acceptor with pH equal to 14",
                        "Proton donor with pH less than 7",
                        "Incapable of conducting electricity"
                    ],
                    "correct_answer": "C",
                    "expected_answer": "Acids are proton donors with a pH less than 7."
                },
                {
                    "question": "Which thermodynamic term describes chemical reactions that release heat to the surroundings?",
                    "options": [
                        "Endothermic reactions",
                        "Exothermic reactions",
                        "Isothermal reactions",
                        "Adiabatic reactions"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Exothermic reactions release thermal energy to the surroundings."
                }
            ],
            "flashcards": [
                {"front": "What is Boyle's Law?", "back": "Pressure and volume of a gas are inversely proportional at constant temperature."},
                {"front": "What is a Covalent Bond?", "back": "A chemical bond formed by the sharing of electron pairs between atoms."},
                {"front": "How does Electronegativity trend across the Periodic Table?", "back": "It increases from left to right across a period and decreases down a group."},
                {"front": "What defines an Acid in aqueous solution?", "back": "A proton (H+) donor with a pH value less than 7."},
                {"front": "What is Charles's Law?", "back": "Gas volume is directly proportional to absolute temperature at constant pressure."},
                {"front": "What is an Exothermic Reaction?", "back": "A reaction that releases thermal energy to the surroundings with negative enthalpy."},
                {"front": "What is Avogadro's Number?", "back": "6.022 x 10^23, representing the number of particles in one mole of a substance."},
                {"front": "What is Neutralization?", "back": "Reaction between an acid and a base producing a salt and water."}
            ]
        },

        "Physics": {
            "notes": [
                {
                    "text": "Newton's first law of motion states that an object remains at rest or in uniform velocity unless acted upon by a net external force.",
                    "tag": "Definition"
                },
                {
                    "text": "Newton's second law states that acceleration is directly proportional to net force and inversely proportional to mass, expressed as F equals m a.",
                    "tag": "Important"
                },
                {
                    "text": "For example, pushing an empty shopping cart produces much greater acceleration than pushing a fully loaded cart with the same force.",
                    "tag": "Example"
                },
                {
                    "text": "Newton's third law states that when one body exerts a force on a second body, the second body exerts an equal and opposite force on the first.",
                    "tag": "Definition"
                },
                {
                    "text": "Kinetic energy is the energy possessed by an object due to its motion, calculated as one-half mass times velocity squared.",
                    "tag": "Definition"
                },
                {
                    "text": "The first law of thermodynamics states that energy cannot be created or destroyed, only transformed from one form to another.",
                    "tag": "Important"
                },
                {
                    "text": "Ohm's law states that electrical current flowing through a conductor is directly proportional to voltage and inversely proportional to resistance.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, stepping off a boat pushes the boat backwards into the water as your feet push forward.",
                    "tag": "Example"
                }
            ],
            "quiz": [
                {
                    "question": "What is the mathematical formulation of Newton's second law of motion?",
                    "options": [
                        "F = m * a",
                        "E = m * c^2",
                        "V = I * R",
                        "P = V * I"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "Force equals mass times acceleration (F = m * a)."
                },
                {
                    "question": "What does Newton's third law of motion assert?",
                    "options": [
                        "Energy is conserved in all closed systems.",
                        "For every action force, there is an equal and opposite reaction force.",
                        "Objects in motion will naturally decelerate.",
                        "Acceleration decreases with increasing velocity."
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Every action has an equal and opposite reaction."
                },
                {
                    "question": "How is kinetic energy calculated for an object with mass m and velocity v?",
                    "options": [
                        "m * g * h",
                        "1/2 * m * v^2",
                        "m * v",
                        "F * d"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Kinetic energy equals one half mass times velocity squared."
                },
                {
                    "question": "What principle is expressed by the first law of thermodynamics?",
                    "options": [
                        "Entropy of an isolated system always increases.",
                        "Energy cannot be created or destroyed, only transformed.",
                        "Absolute zero is impossible to reach in finite steps.",
                        "Heat flows spontaneously from cold to hot bodies."
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Conservation of energy: energy cannot be created or destroyed."
                },
                {
                    "question": "According to Ohm's law, what is the relationship between voltage V, current I, and resistance R?",
                    "options": [
                        "V = I * R",
                        "I = V * R",
                        "R = V * I",
                        "V = I / R"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "Voltage equals current multiplied by resistance (V = I * R)."
                }
            ],
            "flashcards": [
                {"front": "What is Newton's First Law of Motion?", "back": "An object remains at rest or in uniform velocity unless acted upon by a net external force."},
                {"front": "What is Newton's Second Law of Motion?", "back": "Force equals mass times acceleration: F = m * a."},
                {"front": "What is Newton's Third Law of Motion?", "back": "For every action force, there is an equal and opposite reaction force."},
                {"front": "What is Kinetic Energy?", "back": "Energy of motion, calculated as 1/2 * m * v^2."},
                {"front": "What is the First Law of Thermodynamics?", "back": "Conservation of energy: energy cannot be created or destroyed, only transformed."},
                {"front": "What is Ohm's Law?", "back": "Electrical current is directly proportional to voltage and inversely proportional to resistance: V = I * R."},
                {"front": "What is Gravitational Potential Energy?", "back": "Energy stored by virtue of an object's position in a gravitational field: PE = m * g * h."},
                {"front": "What is Work in physics?", "back": "Work is force applied over a distance in the direction of the force: W = F * d."}
            ]
        },

        "Computer Science": {
            "notes": [
                {
                    "text": "General overview: Computer science encompasses the theoretical foundations of computation, algorithms, data structures, and software engineering systems.",
                    "tag": "General"
                },
                {
                    "text": "General overview: Operating systems manage computer hardware, process scheduling, virtual memory management, and file system storage.",
                    "tag": "General"
                },
                {
                    "text": "A binary search algorithm finds the position of a target value within a sorted array in O of log N time complexity.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, binary search on a sorted list of 1,000 items requires at most 10 comparisons.",
                    "tag": "Example"
                },
                {
                    "text": "Quicksort is an efficient divide-and-conquer sorting algorithm with an average time complexity of O of N log N.",
                    "tag": "Definition"
                },
                {
                    "text": "Important exam point: A hash map provides average O of 1 time complexity for insertions, deletions, and key lookups.",
                    "tag": "Important"
                },
                {
                    "text": "Important exam point: The CAP theorem proves that distributed databases can guarantee at most two of: Consistency, Availability, and Partition tolerance.",
                    "tag": "Important"
                },
                {
                    "text": "Polymorphism is an object-oriented programming principle allowing objects of different classes to respond to the same method interface.",
                    "tag": "Definition"
                },
                {
                    "text": "Recursion is a programming technique where a function solves a problem by calling itself with smaller inputs until reaching a base case.",
                    "tag": "Definition"
                },
                {
                    "text": "Relational databases organize structured data into tables of rows and columns with primary and foreign key constraints.",
                    "tag": "Important"
                },
                {
                    "text": "For example, calculating factorial of n recursively returns n multiplied by factorial of n minus 1 with base case factorial of 0 equals 1.",
                    "tag": "Example"
                }
            ],
            "quiz": [
                {
                    "question": "What is the worst-case time complexity of binary search on a sorted array of size N?",
                    "options": [
                        "O(1)",
                        "O(log N)",
                        "O(N)",
                        "O(N^2)"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Binary search runs in O(log N) time complexity."
                },
                {
                    "question": "What is the average time complexity of search operations in a well-distributed hash map?",
                    "options": [
                        "O(1)",
                        "O(log N)",
                        "O(N)",
                        "O(N log N)"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "Average lookup in a hash map is O(1) constant time."
                },
                {
                    "question": "Which OOP concept allows different classes to implement methods with the same signature in distinct ways?",
                    "options": [
                        "Encapsulation",
                        "Polymorphism",
                        "Inheritance",
                        "Composition"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Polymorphism allows different objects to respond to the same method call."
                },
                {
                    "question": "What must every valid recursive function include to prevent infinite loops and stack overflow?",
                    "options": [
                        "A database connection",
                        "A base case",
                        "A foreign key",
                        "A while loop"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Every recursive function requires a terminating base case."
                },
                {
                    "question": "What is the average-case time complexity of the Quicksort algorithm?",
                    "options": [
                        "O(N)",
                        "O(N log N)",
                        "O(N^2)",
                        "O(2^N)"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Quicksort has an average time complexity of O(N log N)."
                }
            ],
            "flashcards": [
                {"front": "What is Binary Search?", "back": "An algorithm that finds a target in a sorted array by repeatedly dividing the search interval in half in O(log N)."},
                {"front": "What is a Hash Map?", "back": "A data structure mapping keys to values using a hash function, providing O(1) average lookup."},
                {"front": "What is Polymorphism in OOP?", "back": "The ability of different classes to be treated through a common interface with specialized method implementations."},
                {"front": "What is Recursion?", "back": "A method where the solution depends on solutions to smaller instances of the same problem, stopping at a base case."},
                {"front": "What is Quicksort?", "back": "A divide-and-conquer sorting algorithm that partitions elements around a pivot with O(N log N) average complexity."},
                {"front": "What is Big O Notation?", "back": "Mathematical notation describing the limiting behavior and efficiency of an algorithm in terms of time or memory."},
                {"front": "What is a Binary Search Tree (BST)?", "back": "A tree data structure where each node has at most two children, with left keys smaller and right keys larger than the node."},
                {"front": "What is SQL?", "back": "Structured Query Language, used to manage and query relational database management systems."}
            ]
        },

        "Mathematics": {
            "notes": [
                {
                    "text": "The derivative of a function measures the instantaneous rate of change of the function with respect to its variable.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, by the power rule, the derivative of x cubed with respect to x is three x squared.",
                    "tag": "Example"
                },
                {
                    "text": "The fundamental theorem of calculus establishes the inverse relationship between differentiation and integration.",
                    "tag": "Important"
                },
                {
                    "text": "The Pythagorean theorem states that in a right-angled triangle, the square of the hypotenuse equals the sum of the squares of the other two sides.",
                    "tag": "Definition"
                },
                {
                    "text": "Bayes' theorem calculates conditional probability of an event based on prior knowledge of related conditions.",
                    "tag": "Important"
                },
                {
                    "text": "An eigenvalue is a scalar lambda that satisfies matrix A times vector v equals lambda times vector v for a non-zero eigenvector v.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, a triangle with legs of length 3 and 4 has a hypotenuse of length 5 since 9 plus 16 equals 25.",
                    "tag": "Example"
                },
                {
                    "text": "Definite integration computes the accumulated signed area under a curve between two specified boundary values.",
                    "tag": "Definition"
                }
            ],
            "quiz": [
                {
                    "question": "What is the derivative of f(x) = x^4 with respect to x?",
                    "options": [
                        "4 * x^3",
                        "x^3",
                        "3 * x^4",
                        "4 * x^5"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "Using the power rule, the derivative of x^4 is 4 * x^3."
                },
                {
                    "question": "What does the Pythagorean theorem state for right triangles with legs a, b and hypotenuse c?",
                    "options": [
                        "a^2 + b^2 = c^2",
                        "a + b = c",
                        "a * b = c^2",
                        "a^2 - b^2 = c^2"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "The sum of the squares of the legs equals the square of the hypotenuse: a^2 + b^2 = c^2."
                },
                {
                    "question": "What fundamental relationship does the Fundamental Theorem of Calculus prove?",
                    "options": [
                        "Addition and subtraction are opposites.",
                        "Differentiation and integration are inverse operations.",
                        "Every polynomial has real roots.",
                        "Area cannot be computed mathematically."
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Differentiation and integration are inverse operations."
                },
                {
                    "question": "Which mathematical theorem expresses conditional probability P(A|B) using P(B|A) and prior probabilities?",
                    "options": [
                        "Central Limit Theorem",
                        "Bayes' Theorem",
                        "Fermat's Last Theorem",
                        "Pythagorean Theorem"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Bayes' theorem describes conditional probability."
                },
                {
                    "question": "What scalar quantity satisfies the equation A * v = lambda * v for a square matrix A and non-zero vector v?",
                    "options": [
                        "Determinant",
                        "Eigenvalue",
                        "Trace",
                        "Cross product"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "The scalar lambda is called an eigenvalue of matrix A."
                }
            ],
            "flashcards": [
                {"front": "What is a Derivative in calculus?", "back": "The instantaneous rate of change of a function with respect to one of its variables."},
                {"front": "What is the Power Rule for differentiation?", "back": "The derivative of x^n with respect to x is n * x^(n - 1)."},
                {"front": "What is the Fundamental Theorem of Calculus?", "back": "It connects differentiation and integration, showing they are inverse processes."},
                {"front": "What is the Pythagorean Theorem?", "back": "In a right triangle: a^2 + b^2 = c^2, where c is the hypotenuse."},
                {"front": "What is Bayes' Theorem?", "back": "A mathematical formula for determining conditional probability: P(A|B) = [P(B|A) * P(A)] / P(B)."},
                {"front": "What is an Eigenvalue?", "back": "A scalar lambda such that A * v = lambda * v for a non-zero eigenvector v."},
                {"front": "What is a Definite Integral?", "back": "The limit of a sum calculating the net accumulated area under a function curve between two limits."},
                {"front": "What is Matrix Multiplication?", "back": "A binary operation producing a single matrix from two matrices by taking dot products of rows and columns."}
            ]
        },

        "History": {
            "notes": [
                {
                    "text": "The Treaty of Versailles was the primary peace treaty signed in June 1919 that officially concluded World War I between Germany and the Allied Powers.",
                    "tag": "Definition"
                },
                {
                    "text": "Important exam point: The Treaty of Versailles imposed heavy financial reparations and territorial losses on Germany, which contributed to political instability.",
                    "tag": "Important"
                },
                {
                    "text": "The Industrial Revolution was the transition to new manufacturing processes in Great Britain, continental Europe, and the United States from around 1760 to 1840.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, James Watt's improved steam engine drastically increased factory productivity and powered locomotives and steamboats.",
                    "tag": "Example"
                },
                {
                    "text": "World War II was a global conflict from 1939 to 1945 fought between the Allied Powers, led by Britain, the US, and the USSR, and the Axis Powers.",
                    "tag": "Definition"
                },
                {
                    "text": "D-Day on June 6, 1944 was the Allied amphibious invasion of Normandy, France, opening the Western Front against Nazi Germany.",
                    "tag": "Important"
                },
                {
                    "text": "The Renaissance was a cultural movement spanning the 14th to 17th centuries marked by a revival of classical learning, art, and humanism in Europe.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, Johannes Gutenberg's movable type printing press in 1440 revolutionized the spread of literacy and scientific knowledge.",
                    "tag": "Example"
                }
            ],
            "quiz": [
                {
                    "question": "Which peace treaty concluded World War I in June 1919?",
                    "options": [
                        "Treaty of Versailles",
                        "Treaty of Paris",
                        "Geneva Convention",
                        "Treaty of Ghent"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "The Treaty of Versailles officially concluded World War I."
                },
                {
                    "question": "What technological innovation improved by James Watt was a central catalyst of the Industrial Revolution?",
                    "options": [
                        "The steam engine",
                        "The cotton gin",
                        "The electric battery",
                        "The telegraph"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "The steam engine powered industrialization and transport."
                },
                {
                    "question": "What historic Allied invasion occurred on June 6, 1944 on the beaches of Normandy?",
                    "options": [
                        "Battle of Midway",
                        "D-Day Invasion",
                        "Battle of Stalingrad",
                        "Pearl Harbor"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "D-Day was the Allied invasion of Normandy, France."
                },
                {
                    "question": "What 1440 European invention by Johannes Gutenberg revolutionized the dissemination of knowledge?",
                    "options": [
                        "Movable type printing press",
                        "The mechanical clock",
                        "The astrolabe",
                        "The water wheel"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "The movable type printing press enabled mass literacy."
                },
                {
                    "question": "Which cultural movement marked the revival of classical art, philosophy, and humanism beginning in 14th-century Italy?",
                    "options": [
                        "The Enlightenment",
                        "The Renaissance",
                        "The Reformation",
                        "The Dark Ages"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "The Renaissance was the revival of classical learning and art."
                }
            ],
            "flashcards": [
                {"front": "What was the Treaty of Versailles?", "back": "The 1919 peace treaty that ended World War I, placing severe reparations and restrictions on Germany."},
                {"front": "What was the Industrial Revolution?", "back": "The transition from agrarian manual labor to machine-driven factory manufacturing between 1760 and 1840."},
                {"front": "What was D-Day in World War II?", "back": "June 6, 1944: The Allied amphibious landing in Normandy, France, opening the Western European front."},
                {"front": "What was the Renaissance?", "back": "A European cultural rebirth of classical learning, art, science, and humanism from the 14th to 17th centuries."},
                {"front": "What impact did Gutenberg's Printing Press have?", "back": "Invented in 1440, it enabled mass publication of books, democratizing literacy and scientific knowledge."},
                {"front": "What were the two opposing alliances in World War II?", "back": "The Allied Powers (US, UK, USSR, China) versus the Axis Powers (Germany, Japan, Italy)."},
                {"front": "What was the Cold War?", "back": "A prolonged ideological, geopolitical, and economic rivalry between the US and the USSR from 1947 to 1991."},
                {"front": "What was the significance of the Steam Engine?", "back": "Improved by James Watt, it provided mechanical power for factories, locomotives, and steamships."}
            ]
        },

        "Geography": {
            "notes": [
                {
                    "text": "General overview: Geography bridges natural physical sciences with human social systems by studying Earth's landscapes, environments, and spatial patterns.",
                    "tag": "General"
                },
                {
                    "text": "General overview: Earth's atmosphere consists of five primary layers: the troposphere where weather happens, stratosphere with the ozone layer, mesosphere, thermosphere, and exosphere.",
                    "tag": "General"
                },
                {
                    "text": "General overview: Global climate zones range from equatorial tropical rain forests to arid desert biomes and high-latitude arctic tundra.",
                    "tag": "General"
                },
                {
                    "text": "Important exam point: Plate tectonics explains continental drift, seismic fault lines, and volcanic mountain building at lithospheric plate boundaries.",
                    "tag": "Important"
                },
                {
                    "text": "Important exam point: The Prime Meridian at Greenwich defines zero degrees longitude, while the Equator defines zero degrees latitude for global timekeeping and navigation.",
                    "tag": "Important"
                },
                {
                    "text": "Important exam point: The Pacific Ring of Fire contains over 75 percent of Earth's active volcanoes and generates 90 percent of all earthquakes.",
                    "tag": "Important"
                },
                {
                    "text": "Plate tectonics is the scientific theory explaining how Earth's subterranean lithospheric plates move, interact, and create major landforms.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, the collision of the Indian Plate with the Eurasian Plate formed the Himalayan mountain range and continues to cause seismic activity.",
                    "tag": "Example"
                }
            ],
            "quiz": [
                {
                    "question": "What geophysical theory explains the movement of Earth's lithospheric plates across the asthenosphere?",
                    "options": [
                        "Plate tectonics",
                        "Continental erosion",
                        "Glacial deposition",
                        "Tidal oscillation"
                    ],
                    "correct_answer": "A",
                    "expected_answer": "Plate tectonics explains lithospheric motion and landform creation."
                },
                {
                    "question": "Which imaginary meridian represents zero degrees longitude and coordinates international standard time?",
                    "options": [
                        "Equator",
                        "Prime Meridian",
                        "Tropic of Cancer",
                        "International Date Line"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "The Prime Meridian at Greenwich represents zero degrees longitude."
                },
                {
                    "question": "Which atmospheric layer closest to Earth contains almost all meteorological weather events?",
                    "options": [
                        "Stratosphere",
                        "Mesosphere",
                        "Troposphere",
                        "Thermosphere"
                    ],
                    "correct_answer": "C",
                    "expected_answer": "The troposphere contains nearly all clouds and weather events."
                },
                {
                    "question": "What tectonic zone around the Pacific basin accounts for over 75 percent of Earth's active volcanoes?",
                    "options": [
                        "Mid-Atlantic Ridge",
                        "Ring of Fire",
                        "Great Rift Valley",
                        "San Andreas Fault"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "The Pacific Ring of Fire contains over 75% of active volcanoes."
                },
                {
                    "question": "What type of plate boundary occurs where two tectonic plates move apart from each other?",
                    "options": [
                        "Convergent boundary",
                        "Divergent boundary",
                        "Transform fault",
                        "Subduction trench"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Divergent boundaries occur where plates move apart, causing seafloor spreading."
                }
            ],
            "flashcards": [
                {"front": "What is Plate Tectonics?", "back": "The geophysical theory that Earth's outer lithosphere is divided into plates moving across the ductile asthenosphere."},
                {"front": "What is the Prime Meridian?", "back": "The meridian at 0 degrees longitude passing through Greenwich, England, coordinating international time."},
                {"front": "What is the Equator?", "back": "The imaginary circle at 0 degrees latitude equidistant from both poles, dividing Northern and Southern hemispheres."},
                {"front": "What is the Ring of Fire?", "back": "A horseshoe-shaped circum-Pacific belt where over 75% of volcanoes and 90% of earthquakes occur."},
                {"front": "What are the five layers of the Atmosphere?", "back": "Troposphere, Stratosphere (with ozone layer), Mesosphere, Thermosphere, and Exosphere."},
                {"front": "What is a Divergent Boundary?", "back": "A tectonic boundary where plates pull apart, causing seafloor spreading at mid-ocean ridges."},
                {"front": "What is a Convergent Boundary?", "back": "A tectonic boundary where plates collide, causing subduction trenches, earthquakes, and mountain ranges."},
                {"front": "What is Topography?", "back": "The study and mapping of elevation, relief, and physical surface features of an area."}
            ]
        },

        "Biology": {
            "notes": [
                {
                    "text": "General overview: Biology is the natural science that studies life and living organisms, including their physical structure and cellular processes.",
                    "tag": "General"
                },
                {
                    "text": "General overview: DNA stores hereditary genetic instructions in a double helix structure composed of adenine, thymine, cytosine, and guanine base pairs.",
                    "tag": "General"
                },
                {
                    "text": "Mitosis is the process of cell division resulting in two genetically identical diploid daughter cells.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, human skin cells and stem cells divide continuously through mitosis to replace damaged tissue.",
                    "tag": "Example"
                },
                {
                    "text": "Remember that the mitochondria is the powerhouse of the cell, generating adenosine triphosphate through oxidative phosphorylation.",
                    "tag": "Important"
                },
                {
                    "text": "Important exam point: Cellular respiration occurs in mitochondria where glucose oxidation produces 36 to 38 ATP molecules per glucose molecule.",
                    "tag": "Important"
                },
                {
                    "text": "Photosynthesis is the biochemical process by which green plant cells convert sunlight, water, and carbon dioxide into glucose and oxygen.",
                    "tag": "Definition"
                },
                {
                    "text": "For example, enzymes act as biological catalysts lowering activation energy to accelerate metabolic reactions in living systems.",
                    "tag": "Example"
                }
            ],
            "quiz": [
                {
                    "question": "What biological process results in two genetically identical diploid daughter cells?",
                    "options": [
                        "Meiosis",
                        "Mitosis",
                        "Fertilization",
                        "Translation"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Mitosis produces two genetically identical diploid daughter cells."
                },
                {
                    "question": "Which cellular organelle is known as the powerhouse of the cell for synthesizing ATP?",
                    "options": [
                        "Nucleus",
                        "Mitochondria",
                        "Ribosome",
                        "Endoplasmic reticulum"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Mitochondria generate cellular energy in the form of ATP."
                },
                {
                    "question": "What green pigment inside plant chloroplasts captures solar photon energy for photosynthesis?",
                    "options": [
                        "Hemoglobin",
                        "Chlorophyll",
                        "Melanin",
                        "Carotene"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Chlorophyll captures light energy to power photosynthesis."
                },
                {
                    "question": "How many total chromosomes are contained in normal human somatic diploid cells?",
                    "options": [
                        "23 chromosomes",
                        "46 chromosomes",
                        "92 chromosomes",
                        "12 chromosomes"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Human somatic cells have 46 chromosomes organized into 23 pairs."
                },
                {
                    "question": "Which nitrogenous base pairs with adenine in DNA double helix molecules?",
                    "options": [
                        "Uracil",
                        "Thymine",
                        "Cytosine",
                        "Guanine"
                    ],
                    "correct_answer": "B",
                    "expected_answer": "Thymine pairs with adenine in DNA (A pairs with T)."
                }
            ],
            "flashcards": [
                {"front": "What is Mitosis?", "back": "A type of cell division resulting in two genetically identical diploid daughter cells."},
                {"front": "What is the function of Mitochondria?", "back": "Powerhouse of the cell, generating ATP energy via oxidative phosphorylation."},
                {"front": "What is Photosynthesis?", "back": "Biochemical process in plant chloroplasts converting solar light, water, and CO2 into glucose and oxygen."},
                {"front": "What is the Central Dogma of biology?", "back": "Genetic information flows from DNA to RNA via transcription, and RNA to protein via translation."},
                {"front": "What is Meiosis?", "back": "Specialized cell division producing four genetically distinct haploid gametes with half the chromosome count."},
                {"front": "What is an Enzyme?", "back": "A biological protein catalyst that lowers activation energy to speed up metabolic reactions."},
                {"front": "What is Osmosis?", "back": "Passive diffusion of water molecules across a selectively permeable membrane toward higher solute concentration."},
                {"front": "What is the difference between DNA and RNA?", "back": "DNA is double-stranded with deoxyribose and thymine; RNA is single-stranded with ribose and uracil."}
            ]
        }
    }

    @classmethod
    def match_subject(cls, topic: str) -> Optional[str]:
        """
        Maps a requested topic to a recognized curriculum subject.
        """
        if not topic:
            return None
        import re
        topic_lower = topic.strip().lower()
        words = set(re.findall(r"\b\w+\b", topic_lower))
        if words.intersection({"chemistry", "chemist", "chem", "boyle", "reaction", "acid", "molecule", "bond"}):
            return "Chemistry"
        if words.intersection({"physics", "physic", "newton", "gravity", "thermodynamics", "optics"}):
            return "Physics"
        if words.intersection({"cs", "comp", "computer", "code", "algorithm", "python", "programming", "algorithms"}):
            return "Computer Science"
        if words.intersection({"math", "mathematics", "calculus", "derivative", "integral", "algebra", "pythagoras", "pythagorean"}):
            return "Mathematics"
        if words.intersection({"history", "historical", "versailles", "revolution", "renaissance"}):
            return "History"
        if words.intersection({"biology", "biologist", "bio", "mitosis", "photosynthesis", "genetics"}):
            return "Biology"
        if words.intersection({"geography", "geographic", "geology", "tectonics", "earth", "climate", "latitude", "longitude", "atmosphere"}):
            return "Geography"

        return None

    @classmethod
    def generate_and_store_materials(cls, user_id: str, topic: str, gemini_service=None) -> Optional[Dict[str, Any]]:
        """
        Generates and permanently stores study notes, quiz questions, and flashcards
        in SQLite for the requested subject or topic.
        Returns dict containing stored notes, quiz, and flashcards, or None if topic unknown.
        """
        clean_topic = topic.strip().title() if topic else "General"
        matched_subject = cls.match_subject(topic)

        # 1. Check if Gemini can generate for any custom topic
        if gemini_service and gemini_service.is_available():
            try:
                gemini_notes = gemini_service.generate_notes_for_topic(clean_topic)
                if gemini_notes and len(gemini_notes) > 0:
                    stored = cls._store_notes_and_flashcards(user_id, clean_topic, gemini_notes)
                    quiz = gemini_service.generate_mcq_quiz(clean_topic, stored["notes"])
                    flashcards = gemini_service.generate_flashcards(clean_topic, stored["notes"])
                    return {
                        "subject": clean_topic,
                        "notes": stored["notes"],
                        "quiz": quiz,
                        "flashcards": flashcards,
                        "source": "gemini"
                    }
            except Exception as e:
                pass

        # 2. Local curriculum fallback for recognized subjects
        if matched_subject and matched_subject in cls.CURRICULUM:
            curriculum_data = cls.CURRICULUM[matched_subject]
            stored = cls._store_notes_and_flashcards(user_id, matched_subject, curriculum_data["notes"], curriculum_data["flashcards"])
            return {
                "subject": matched_subject,
                "notes": stored["notes"],
                "quiz": {
                    "type": "quiz",
                    "topic": matched_subject,
                    "questions": curriculum_data["quiz"]
                },
                "flashcards": {
                    "type": "flashcards",
                    "topic": matched_subject,
                    "cards": curriculum_data["flashcards"]
                },
                "source": "curriculum"
            }

        return None

    @classmethod
    def _store_notes_and_flashcards(cls, user_id: str, subject: str, notes_list: List[Dict[str, Any]], 
                                    flashcards_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Persists generated notes and flashcards into SQLite database.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        now_dt = datetime.now()
        now_iso = now_dt.isoformat()
        time_str = now_dt.strftime("%I:%M %p")

        stored_notes = []
        for n in notes_list:
            text = n["text"]
            tag = n.get("tag", "Definition")
            
            # Check if this exact note already exists to prevent duplicate spam
            cursor.execute("SELECT * FROM notes WHERE user_id = ? AND text = ? AND is_deleted = 0", (user_id, text))
            existing = cursor.fetchone()
            if existing:
                stored_notes.append(dict(existing))
                continue

            note_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO notes (note_id, user_id, session_id, subject, text, tag, timestamp, confidence, created_at, updated_at, is_deleted)
                VALUES (?, ?, NULL, ?, ?, ?, ?, 1.0, ?, ?, 0)
            """, (note_id, user_id, subject, text, tag, time_str, now_iso, now_iso))
            
            stored_notes.append({
                "note_id": note_id,
                "user_id": user_id,
                "subject": subject,
                "text": text,
                "tag": tag,
                "timestamp": time_str,
                "confidence": 1.0
            })

        # Store flashcards linked to notes
        if flashcards_list:
            for idx, fc in enumerate(flashcards_list):
                front = fc["front"]
                back = fc["back"]
                source_note_id = stored_notes[idx % len(stored_notes)]["note_id"] if stored_notes else None

                cursor.execute("SELECT * FROM flashcards WHERE user_id = ? AND question = ?", (user_id, front))
                if not cursor.fetchone():
                    fc_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO flashcards (id, source_note_id, user_id, subject, tag, question, answer, difficulty, review_count, correct_count)
                        VALUES (?, ?, ?, ?, 'Definition', ?, ?, 'Medium', 0, 0)
                    """, (fc_id, source_note_id, user_id, subject, front, back))

        conn.commit()
        conn.close()
        return {"notes": stored_notes}
