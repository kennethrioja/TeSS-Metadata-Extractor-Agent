# Material: Resource type list

Scraped from ELIXIR TeSS, on May 12, 2026, n=89:

```json
[
  "e-learning",
  "Recorded webinar",
  "slides",
  "Video",
  "Tutorial",
  "Training materials",
  "Presentation",
  "Course materials",
  "Webinar",
  "lessons",
  "tutorial",
  "Slides",
  "hands-on tutorial",
  "video",
  "Slidedeck",
  "Documentation",
  "course materials",
  "exercise",
  "Scripts",
  "Exercise",
  "Handout",
  "Lecture",
  "E-learning",
  "PDF",
  "E-Learning",
  "Online material",
  "Bioinformatics",
  "Coding",
  "FREE online course",
  "Talk",
  "tutorials",
  "youtube video",
  " Series of videos",
  "Jupyter notebook",
  "online course",
  "online modules",
  "Book",
  "Computational Biology",
  "Computer Science",
  "Computer Software",
  "Data Science",
  "Education",
  "How-to guide",
  "Life Sciences Literature Database",
  "Mock data",
  "Programming",
  "examples",
  "online tutorial",
  "slideck/ presentation",
  "API reference",
  "Installation instructions",
  "Learning pathway",
  "Manual",
  "Open educational resource",
  "Poster",
  "Series of videos",
  "Vignette",
  "case studies",
  "e-Learning",
  "educational materials",
  "handbook",
  "knowledgebase",
  "presentation",
  "scripts",
  "workflow",
  "Blog post",
  "Carpentries style curriculum",
  "E-learning + workshop",
  "Educational Resource",
  "Jupyter notebooks",
  "Life Science Literature Database",
  "Machine Learning",
  "Notes",
  "R Shiny application",
  "Recording",
  "Slideshow",
  "Tool",
  "Toolkit",
  "Training materials with mock data",
  "Transcriptomics",
  "ViralZone",
  "Workshop",
  "additional reading",
  "didactic activities",
  "hackathon",
  "implementation guidelines",
  "podcast",
  "slide deck / presentation",
  "slides / presentation"
]
```

Removing duplicates (n=11):
```json
[
    "tutorial",
    "Slides",
    "video",
    "course materials",
    "Exercise",
    "E-learning",
    "E-Learning",
    "e-Learning",
    "presentation",
    "scripts",
    "Series of videos"
]
```

Removing all words which cannot be categorized under 'Training Material Type' (n=19)

```json
[
  "Online material",
  "Bioinformatics",
  "Coding",
  "Talk",
  "Computational Biology",
  "Computer Science",
  "Computer Software",
  "Data Science",
  "Education",
  "Life Sciences Literature Database",
  "Programming",
  "knowledgebase",
  "Life Science Literature Database",
  "Machine Learning",
  "Notes",
  "R Shiny application",
  "Transcriptomics",
  "ViralZone",
  "hackathon",
  "implementation guidelines"
]
```

Agregating words from the same family under the same umbrella, e.g., video, youtube video, series of videos -> Video

```json
{
  "E-learning": [
    "e-learning",
    "FREE online course",
    "online course",
    "online modules",
    "E-learning + workshop"
  ],
  "Webinar": [
    "Webinar",
    "Recorded webinar",
    "Recording"
  ],
  "Slides": [
    "slides",
    "Slidedeck",
    "Slideshow",
    "slide deck / presentation",
    "slides / presentation",
    "slideck/ presentation"
  ],
  "Video": [
    "Video",
    "youtube video",
    "Series of videos"
  ],
  "Tutorial": [
    "Tutorial",
    "tutorials",
    "hands-on tutorial",
    "online tutorial",
    "Jupyter notebook",
    "Jupyter notebooks"
  ],
  "Course Materials": [
    "Course materials",
    "Training materials",
    "Training materials with mock data",
    "educational materials",
    "Educational Resource",
    "Carpentries style curriculum",
    "Open educational resource"
  ],
  "Presentation": [
    "Presentation",
    "Poster",
    "Talk"
  ],
  "Lessons": [
    "lessons",
    "didactic activities"
  ],
  "Documentation": [
    "Documentation",
    "Manual",
    "handbook",
    "workflow",
    "Vignette",
    "Blog post"
  ],
  "Exercise": [
    "exercise",
    "examples",
    "Mock data"
  ],
  "Guide": [
    "How-to guide",
    "additional reading",
    "implementation guidelines"
  ],
  "Reference Material": [
    "API reference",
    "Installation instructions",
    "PDF",
    "Book",
    "Toolkit",
    "Tool"
  ],
  "Case Study": [
    "case studies"
  ],
  "Workshop": [
    "Workshop",
    "hackathon"
  ],
  "Podcast": [
    "podcast"
  ]
}
```

Decided to keep "poster", "handbook" and "blog post", which leads to this final list of 17 words:

```json
[
    "Blog post",
    "Case Study",
    "Course Materials",
    "Documentation",
    "E-learning",
    "Exercise",
    "Guide",
    "Handbook",
    "Lessons",
    "Podcast",
    "Poster",
    "Presentation",
    "Reference Material",
    "Slides",
    "Tutorial",
    "Video",
    "Webinar",
    "Workshop"
]
```
