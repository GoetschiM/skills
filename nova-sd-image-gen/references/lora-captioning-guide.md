# SD 1.5 LoRA Captioning Guide

Consistent captions are the single most important factor for LoRA quality.
A badly captioned dataset produces a blurry, inconsistent LoRA — no matter how long you train.

## Golden Rules

1. **Every image MUST start with the trigger word** — this is what the LoRA learns to associate with your subject.
2. **Keep captions consistent across images** — same descriptors for same features.
3. **Describe what you see, not what you imagine** — "blonde hair" not "golden locks".
4. **Don't caption the background** unless it's relevant — the LoRA should learn the subject, not the setting.

## Caption Format

```
<trigger_word>, <demographics>, <appearance>, <pose>, <expression>, <shot_type>
```

### Example for Leo (3-year-old boy):

```
leo, young boy, 3 years old, blonde hair, blue eyes, smiling, looking at camera, portrait, wearing red t-shirt
```

## Essential Descriptor Categories

| Category | Examples |
|----------|----------|
| **Trigger** | `leo` (must be first word in EVERY caption) |
| **Demographics** | `young boy`, `3 years old`, `toddler` |
| **Hair** | `blonde hair`, `short hair`, `straight hair` |
| **Eyes** | `blue eyes`, `light eyes` |
| **Face** | `round face`, `soft features`, `rosy cheeks` |
| **Pose** | `front view`, `side view`, `looking at camera`, `looking away` |
| **Expression** | `smiling`, `laughing`, `serious`, `surprised` |
| **Shot** | `portrait`, `close-up`, `full body`, `waist up` |
| **Clothing** | `wearing red t-shirt`, `wearing blue jeans` |

## Common Captioning Mistakes

| Mistake | Why It Hurts | Fix |
|---------|-------------|-----|
| Inconsistent hair color | LoRA doesn't know what color Leo's hair is | Use `blonde` on every image |
| Missing trigger word | LoRA doesn't know WHICH subject to learn | Start every caption with `leo,` |
| Too many details | LoRA overfits to specific images | Keep to 5-10 key descriptors |
| Wrong angle description | LoRA expects a front-view face but gets profile | Be honest: `profile view` if true |
| Not captioning emotion | LoRA generates neutral faces only | Add `smiling` / `laughing` etc. |

## Photo Requirements for Best Results

| Aspect | Requirement |
|--------|-------------|
| **Count** | 10-20 images minimum |
| **Resolution** | At least 512×512 (will be center-cropped) |
| **Lighting** | Consistent, well-lit — avoid harsh shadows |
| **Variety** | Different angles (front, 3/4, profile), expressions (smiling, neutral), backgrounds |
| **File format** | JPG or PNG |
| **Naming** | `leo_01.jpg`, `leo_02.jpg` — avoid spaces in filenames |

## Example Caption Set

```
File: leo_01.jpg → "leo, young boy, 3 years old, blonde hair, blue eyes, smiling, front view, looking at camera, portrait, wearing red t-shirt"
File: leo_02.jpg → "leo, young boy, 3 years old, blonde hair, blue eyes, laughing, three-quarter view, outdoors"
File: leo_03.jpg → "leo, young boy, 3 years old, blonde hair, blue eyes, serious, profile view, close-up"
File: leo_04.jpg → "leo, young boy, 3 years old, blonde hair, blue eyes, smiling, full body, standing, playing outside"
```

## Using Hermes Vision for Auto-Captioning

Instead of manual captioning, use Hermes' `vision_analyze` tool on each photo:

```
vision_analyze(image_path="<path>", question="Describe this person in detail: hair color, eye color, age, expression, pose, clothing, angle. Start with the trigger word 'leo'.")
```

Then copy the description into `<image_name>.txt`. Verify and correct manually — vision models sometimes hallucinate eye colors or ages.
