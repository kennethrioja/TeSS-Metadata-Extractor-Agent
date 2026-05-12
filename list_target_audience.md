# Material: Target Audience list

Scraped from ELIXIR TeSS, on May 12, 2026.

Step 1: Remove Duplicates (n=13 removed)

Unique List (n=87):

```json
[
  "Students",
  "PhD students",
  "Clinicians",
  "Galaxy Administrators",
  "Researchers",
  "Instructors",
  "Biologists",
  "Life Science Researchers",
  "Novice",
  "bioinformaticians",
  "Intermediate",
  "PhD candidate",
  "Scientific community",
  "PhD candidates",
  "Biologists, Genomicists, Computer Scientists",
  "Scientists",
  "Data stewards",
  "post-docs",
  "Data Managers",
  "Bench biologists",
  "Academia/ Research Institution",
  "Industry",
  "Non-Profit Organisation",
  "Beginners",
  "Data Scientists",
  "Graduate Students",
  "Post-Doctoral Fellows",
  "Trainers",
  "Healthcare",
  "beginner bioinformaticians",
  "Data Scientist",
  "Researcher in life sciences",
  "Master students",
  "Research Scientists",
  "Biomedical Researchers",
  "Computational biologists",
  "software developers, bioinformaticians",
  "Researcher",
  "biocurators",
  "health professionals",
  "Training Designers",
  "Training instructors",
  "healthcare professionals",
  "Beginner",
  "Bioinformatician",
  "Life scientists with programming skills",
  "PhD",
  "Post Docs",
  "modelers",
  "Health Care Professionals",
  "Chemists",
  "Clinical Scientists",
  "General Interest",
  "PI",
  "Patient Advocates",
  "Undergraduate students",
  "computational scientists",
  "postgrad",
  "project manager",
  "rare disease patients representatives",
  "Anyone wishing to use bioinformatics resources to find basic information about a virus.",
  "Biologists with little or no prior computational experience",
  "Curators",
  "Laboratory technicians",
  "PhD Scholars, Graduates and Post Graduates, Professors, Associate Professors, Assistant Professors, Bio instruments Professionals, Bio-informatics Professionals, Directors, CEO’s of Organizations, Supply Chain companies, Manufacturing Companies, Software development companies, Research Institutes and members",
  "Postgraduate students",
  "Veterinarians",
  "plant researchers",
  "postdocs",
  "Bioinformatician, Bioanalysts",
  "Data Steward",
  "Database users",
  "Ontologists",
  "Researchers and bioinformaticians in other projects interested in depositiong data at the EGA",
  "Technicians",
  "data steward / data manager",
  "geneticists",
  "postdoc",
  "postdoctoral researchers",
  "programmers",
  "software engineers",
  "teachers",
  "Academics",
  "Anyone interested in data standardization and/or the ontology approach (i.e. public, end users).",
  "Anyone interested in simulation of metabolic models, and in PerMedCoE tools and activities",
  "Beginner informatics",
  "Bioinformaticians, Biologists with little or no prior computational experience."
]
```

Duplicates (n=13):

```json
[
  "Bioinformaticians",
  "life scientists",
  "Data managers",
  "PhD Students",
  "data stewards",
  "Biomedical researchers",
  "Life scientists",
  "biologists",
  "Life Scientists",
  "Graduate students",
  "data managers",
  "researchers",
  "life science researchers"
]
```

Step 2: Remove Non-"Target Audience" Words (n=18 removed)

Filtered list (n=69):

```json
[
  "Students",
  "PhD students",
  "Clinicians",
  "Galaxy Administrators",
  "Researchers",
  "Instructors",
  "Biologists",
  "Life Science Researchers",
  "Novice",
  "bioinformaticians",
  "Intermediate",
  "PhD candidate",
  "Scientific community",
  "PhD candidates",
  "Scientists",
  "Data stewards",
  "post-docs",
  "Data Managers",
  "Bench biologists",
  "Beginners",
  "Data Scientists",
  "Graduate Students",
  "Post-Doctoral Fellows",
  "Trainers",
  "Healthcare",
  "Data Scientist",
  "Researcher in life sciences",
  "Master students",
  "Research Scientists",
  "Biomedical Researchers",
  "Computational biologists",
  "Researcher",
  "biocurators",
  "health professionals",
  "Training Designers",
  "Training instructors",
  "healthcare professionals",
  "Beginner",
  "Bioinformatician",
  "PhD",
  "Post Docs",
  "modelers",
  "Health Care Professionals",
  "Chemists",
  "Clinical Scientists",
  "PI",
  "Patient Advocates",
  "Undergraduate students",
  "computational scientists",
  "postgrad",
  "project manager",
  "rare disease patients representatives",
  "Curators",
  "Laboratory technicians",
  "Postgraduate students",
  "Veterinarians",
  "plant researchers",
  "postdocs",
  "Data Steward",
  "Database users",
  "Ontologists",
  "Technicians",
  "geneticists",
  "postdoc",
  "postdoctoral researchers",
  "programmers",
  "software engineers",
  "teachers",
  "Academics"
]
```

Removed items (n=18):

```json
[
  "Biologists, Genomicists, Computer Scientists",
  "Academia/ Research Institution",
  "Industry",
  "Non-Profit Organisation",
  "beginner bioinformaticians",
  "software developers, bioinformaticians",
  "Life scientists with programming skills",
  "General Interest",
  "Anyone wishing to use bioinformatics resources to find basic information about a virus.",
  "Biologists with little or no prior computational experience",
  "PhD Scholars, Graduates and Post Graduates, Professors, Associate Professors, Assistant Professors, Bio instruments Professionals, Bio-informatics Professionals, Directors, CEO’s of Organizations, Supply Chain companies, Manufacturing Companies, Software development companies, Research Institutes and members",
  "Bioinformatician, Bioanalysts",
  "Researchers and bioinformaticians in other projects interested in depositiong data at the EGA",
  "data steward / data manager",
  "Anyone interested in data standardization and/or the ontology approach (i.e. public, end users).",
  "Anyone interested in simulation of metabolic models, and in PerMedCoE tools and activities",
  "Beginner informatics",
  "Bioinformaticians, Biologists with little or no prior computational experience."
]
```

Step 3: Gather Under Family/Umbrella Words (n=15 umbrellas):

```json
{
  "Bioinformatician": [
    "bioinformaticians",
    "Bioinformatician",
    "Computational biologists",
    "computational scientists"
  ],
  "Biologist": [
    "Biologists",
    "Bench biologists",
    "plant researchers"
  ],
  "Clinician": [
    "Clinicians",
    "Healthcare",
    "health professionals",
    "healthcare professionals",
    "Health Care Professionals",
    "Clinical Scientists",
    "Veterarians"
  ],
  "Data Professional": [
    "Data stewards",
    "Data Managers",
    "Data Scientists",
    "Data Scientist",
    "Data Steward",
    "Database users"
  ],
  "Educator": [
    "Instructors",
    "Trainers",
    "Training Designers",
    "Training instructors",
    "teachers"
  ],
  "IT Professional": [
    "Galaxy Administrators",
    "programmers",
    "software engineers"
  ],
  "Life Scientist": [
    "Life Science Researchers",
    "Researcher in life sciences",
    "Biomedical Researchers"
  ],
  "Management": [
    "PI",
    "project manager"
  ],
  "Novice / Intermediate": [
    "Novice",
    "Intermediate",
    "Beginners",
    "Beginner"
  ],
  "Patient Advocate": [
    "Patient Advocates",
    "rare disease patients representatives"
  ],
  "PhD Student": [
    "PhD students",
    "PhD candidate",
    "PhD candidates",
    "PhD"
  ],
  "Postdoc": [
    "post-docs",
    "Post-Doctoral Fellows",
    "Post Docs",
    "postdocs",
    "postdoc",
    "postdoctoral researchers"
  ],
  "Researcher": [
    "Researchers",
    "Scientific community",
    "Scientists",
    "Research Scientists",
    "Researcher",
    "Academics"
  ],
  "Specialist": [
    "biocurators",
    "modelers",
    "Chemists",
    "Curators",
    "Laboratory technicians",
    "Ontologists",
    "Technicians",
    "geneticists"
  ],
  "Student": [
    "Students",
    "Graduate Students",
    "Master students",
    "Undergraduate students",
    "postgrad",
    "Postgraduate students"
  ]
}
```

Decided:
- to keep "Undergraduate Student", "Master Student", "Data Steward", "Data Manager", Data Scientist", "Trainer", "Training Designer", "Training Instructor", "Teacher", "Software Engineer", "Project Manager"
- to remove "Bioinformatician", "Biologist", "Clinician", "Data Professional", "Data professional", "IT Professional", "Life Scientist", "Novice / Intermediate", "Patient Advocate", "Management"
- to add "Research Software Engineer", "Physicist"

Leading to this final list (n=17):

```json
[
    "Data Steward",
    "Data Manager",
    "Data Scientist",
    "Master Student",
    "PhD Student",
    "Physicist",
    "Postdoc",
    "Project Manager",
    "Researcher",
    "Research Software Engineer",
    "Software Engineer",
    "Specialist",
    "Trainer",
    "Training Designer",
    "Training Instructor",
    "Teacher",
    "Undergraduate Student"
]
```