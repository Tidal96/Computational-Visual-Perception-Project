"""Build the editable Part 1 slides from the verified submission files."""
import argparse
import csv
import json
from io import BytesIO
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

INK, TEAL, MUTED, PAPER, LINE = '152B3D', '087362', '4E6475', 'F5F8FA', 'D3DFE5'
WHITE, NAVY, SOFT = 'FFFFFF', '163648', 'E5F3EF'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ['submission', 'analysis', 'figures', 'assets']:
        parser.add_argument('--' + option, type=Path, required=True)
    args = parser.parse_args()
    submission, analysis, figures, assets = args.submission, args.analysis, args.figures, args.assets
    manual = json.loads((analysis / 'manual_selection.json').read_text())
    assert manual['status'] == 'confirmed' and len(set(manual['ids'])) == 10
    selected = manual['ids']
    stats = json.loads((analysis / 'summary.json').read_text())
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.3333), Inches(7.5)
    deck.core_properties.title = 'Mooney Faces | Computational Visual Perception | Part 1'
    deck.core_properties.author = 'Hadis Nouri'
    deck.core_properties.subject = 'Part 1 submission | Depth Anything V2 Small and CLIP ViT-B/32'

    def rect(slide, x, y, w, h, fill):
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(fill)
        shape.line.fill.background()
        return shape

    def text(slide, value, x, y, w, h, size=18, bold=False, color=INK,
             align=PP_ALIGN.LEFT, font='Liberation Sans', url=None):
        shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        frame = shape.text_frame
        frame.clear()
        frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
        frame.word_wrap = True
        for index, line in enumerate(value.split('\n')):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.alignment = align
            paragraph.space_after = Pt(3)
            run = paragraph.add_run()
            run.text = line
            run.font.name, run.font.size, run.font.bold = font, Pt(size), bold
            if url:
                run.hyperlink.address = url
            run.font.color.rgb = RGBColor.from_string(color)
        return shape

    def picture(slide, path, x, y, w, h, *, thumb=None, name=None):
        with Image.open(path) as source:
            width, height = source.size
            stream = str(path)
            if thumb:
                image = source.convert('RGB')
                image.thumbnail((thumb, thumb), Image.Resampling.LANCZOS)
                stream = BytesIO()
                if image.getextrema() == ((0, 255), (0, 255), (0, 255)) and path.parent.name == 'Mooney':
                    image.convert('L').save(stream, 'PNG', optimize=True)
                else:
                    image.save(stream, 'JPEG', quality=92, optimize=True, subsampling=0)
                stream.seek(0)
            scale = min(w / width, h / height)
            dw, dh = width * scale, height * scale
            item = slide.shapes.add_picture(stream, Inches(x + (w - dw) / 2),
                                            Inches(y + (h - dh) / 2),
                                            width=Inches(dw), height=Inches(dh))
            if name:
                item.name = name
            return item

    def page(title, subtitle='', section='PART 1 DELIVERABLES'):
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor.from_string(PAPER)
        rect(slide, .54, .38, .25, .055, TEAL)
        text(slide, section, .91, .27, 11.8, .25, 11, True, TEAL)
        text(slide, title, .55, .68, 12.23, .58, 31, True)
        if subtitle:
            text(slide, subtitle, .56, 1.35, 12.15, .44, 14, False, MUTED)
        rect(slide, .55, 7.04, 12.22, .012, LINE)
        text(slide, 'HADIS NOURI  /  COMPUTATIONAL VISUAL PERCEPTION', .56, 7.15, 10, .19, 9, color=MUTED)
        text(slide, f'{len(deck.slides):02}', 12.13, 7.13, .63, .22, 10, True, TEAL, PP_ALIGN.RIGHT)
        return slide

    def row(slide, values, xs, widths, y, *, size=15, height=.4, bold=False, color=INK):
        for value, x, w in zip(values, xs, widths):
            text(slide, value, x, y, w, height, size, bold, color)

    # 1. Title and the complete team.
    slide = page('Mooney Faces', 'Computational Visual Perception  /  Project Part 1')
    text(slide, 'Face perception under\nbinary shading', .60, 2.17, 6.15, 1.86, 40, True)
    text(slide, 'Hadis Nouri', .63, 4.44, 5.8, .6, 27, True, TEAL)
    text(slide, 'Individual project', .64, 5.16, 5.85, .4, 18, color=MUTED)
    text(slide, '100 photographs · 100 Mooneys · 2 vision systems', .64, 6.03, 6.15, .53, 16)
    for index, kind in enumerate(['Original', 'Mooney']):
        x = 6.74 + 3.06 * index
        picture(slide, submission / kind / '010.png', x, 2.32, 2.94, 2.94, thumb=850)
        text(slide, kind + ' 010', x, 5.46, 2.94, .31, 15, True, align=PP_ALIGN.CENTER)

    # 2. Entire approach on one slide.
    slide = page('Approach and idea', 'How much facial structure survives when an image is reduced to black and white?')
    approach = [
        ('01  Select photographs', 'The dataset contains 100 aligned FFHQ photographs at 1024 × 1024. A screening step favored visible facial structure under directional light and reduced bright background clutter.'),
        ('02  Generate Mooneys', 'Convert to grayscale, apply Gaussian blur (σ = 8 px, 49 px kernel), then threshold the brightest pixels to reach 22% or 28% white. The GUI and CLI share the same generator. Hadis Nouri confirmed the ten pairs on slide 3.'),
        ('03  Compare both versions', 'Run each pretrained model on all 100 originals and all 100 Mooneys. Depth Anything estimates relative depth. CLIP ranks eight text prompts. Compare depth agreement and the rank of face prompts.'),
    ]
    for index, (title, body) in enumerate(approach):
        x = .55 + 4.11 * index
        rect(slide, x, 2.1, 3.98, 4.49, WHITE)
        rect(slide, x, 2.1, 3.98, .065, TEAL)
        text(slide, title, x + .21, 2.42, 3.56, .78, 22, True)
        text(slide, body, x + .21, 3.42, 3.54, 2.8, 18)

    # 3. Exactly 10 originals and 10 corresponding Mooneys on one slide.
    slide = page('Ten selected originals and ten Mooneys', 'Each numbered pair shows the original on the left and its Mooney on the right.')
    for index, stem in enumerate(selected):
        x, y = .56 + (index % 5) * 2.45, 1.96 + (index // 5) * 2.33
        rect(slide, x, y, 2.36, 2.12, WHITE)
        text(slide, stem, x + .08, y + .12, .45, .27, 14, True, TEAL)
        for col, kind in enumerate(['Original', 'Mooney']):
            px = x + .07 + 1.13 * col
            text(slide, kind, px, y + .47, 1.08, .23, 11, True, align=PP_ALIGN.CENTER)
            picture(slide, submission / 'Subset' / kind / f'{stem}.png',
                    px, y + .78, 1.09, 1.09, thumb=450, name=f'Subset/{kind}/{stem}.png')
    text(slide, 'Manual selection confirmed by Hadis Nouri.', .58, 6.65, 12.13, .26, 13, color=MUTED)

    # 4. System declaration and folder mapping.
    slide = page('Vision systems used', 'Both pretrained systems received the same 200 images in the saved Kaggle run.')
    systems = [
        ('Result1', 'Depth Anything V2 Small', 'depth-anything/Depth-Anything-V2-Small-hf',
         'Estimates relative inverse depth from a single image. Each result includes a 16-bit PNG and a color JPEG.'),
        ('Result2', 'CLIP ViT-B/32', 'openai/clip-vit-base-patch32',
         'Ranks eight fixed text prompts by image similarity. Each JSON stores the scores, the top prompt, and the combined share of the two face prompts.'),
    ]
    for index, (folder, title, model, body) in enumerate(systems):
        x = .55 + 6.2 * index
        rect(slide, x, 2.03, 6.01, 4.14, WHITE)
        text(slide, folder, x + .22, 2.29, 5.6, .28, 14, True, TEAL)
        text(slide, title, x + .22, 2.78, 5.56, .51, 24, True)
        text(slide, model, x + .22, 3.45, 5.56, .48, 13, color=MUTED, font='DejaVu Sans Mono')
        text(slide, body, x + .22, 4.21, 5.52, 1.5, 18)
    text(slide, '100 originals and 100 Mooneys processed by each model.', .56, 6.57, 12, .32, 16, True, TEAL)

    # 5–6. Real outputs and aggregate results for system 1.
    slide = page('Result1 · Depth Anything outputs', 'Each depth map is normalized to its own range. Brighter areas show higher relative inverse depth.')
    stages = [('Original input', 'Original'), ('Original depth', 'Result1/Original'),
              ('Mooney input', 'Mooney'), ('Mooney depth', 'Result1/Mooney')]
    examples = json.loads((analysis / 'figure_examples.json').read_text())['depth_examples']
    depth_rows = {r['stem']: r for r in csv.DictReader((analysis / 'depth_metrics.csv').open())}
    for col, (label, directory) in enumerate(stages):
        x = 2.35 + col * 2.58
        text(slide, label, x, 1.92, 2.05, .29, 15, True, align=PP_ALIGN.CENTER)
        for index, stem in enumerate(examples):
            suffix = '_depth_vis.jpg' if directory.startswith('Result1') else '.png'
            path = submission / directory / (stem + suffix)
            picture(slide, path, x, 2.30 + index * 1.51, 2.05, 1.36, thumb=500,
                    name=f'{directory}/{stem}{suffix}')
    for index, stem in enumerate(examples):
        correlation = float(depth_rows[stem]['paired_pearson'])
        text(slide, f'Image {stem}\nr = {correlation:.3f}', .61, 2.66 + index * 1.51, 1.65, .7, 16, True)
    slide = page('Result1 · Depth agreement across 100 pairs',
                 'Pixel-by-pixel Pearson correlation. The control pairs each original with the next Mooney in file order.')
    picture(slide, figures / 'depth_statistics.png', .62, 1.94, 12.03, 4.38, name='Depth correlations across all pairs')
    depth = stats['depth']
    text(slide, f'Paired mean {depth["mean_paired_pearson"]:.3f}    |    Control mean {depth["mean_next_image_control"]:.3f}    |    {depth["paired_above_control_count"]}/100 pairs above control',
         .65, 6.36, 12, .32, 17, True, TEAL)
    text(slide, 'The comparison measures agreement between predictions. Ground-truth depth is unavailable.', .65, 6.77, 12, .25, 12, color=MUTED)

    # 7–8. Real per-image outputs plus aggregate statistics for system 2.
    slide = page('Result2 · CLIP outputs', 'The examples show actual top prompts and combined face-prompt scores from the JSON files.')
    clip_ids = json.loads((analysis / 'figure_examples.json').read_text())['clip_examples']
    for idx, stem in enumerate(clip_ids):
        x = .58 + idx * 3.09
        text(slide, f'Image {stem}', x, 1.93, 2.98, .27, 16, True, TEAL, PP_ALIGN.CENTER)
        for index, kind in enumerate(['Original', 'Mooney']):
            y = 2.32 + index * 2.18
            path = submission / 'Result2' / kind / (stem + '.json')
            result = json.loads(path.read_text())
            picture(slide, submission / kind / (stem + '.png'), x, y, 2.98, 1.33, thumb=500, name=f'{kind}/{stem}.png')
            text(slide, f'{kind}   ·   face share {result["p_face"]:.3f}', x, y + 1.37, 2.98, .23, 12, True, align=PP_ALIGN.CENTER)
            text(slide, result['top1'], x, y + 1.66, 2.98, .39, 11, color=MUTED, align=PP_ALIGN.CENTER)
    slide = page('Result2 · Face prompts across 200 images',
                 'The face score adds the shares of the two face prompts among eight fixed prompts.')
    picture(slide, figures / 'clip_statistics.png', .62, 1.92, 12.03, 4.38, name='CLIP scores across all images')
    original, mooney = stats['clip']['Original'], stats['clip']['Mooney']
    text(slide, f'Face prompt ranked first: {original["face_prompt_top1_count"]}/100 originals and {mooney["face_prompt_top1_count"]}/100 Mooneys',
         .65, 6.31, 12, .33, 17, True, TEAL)
    text(slide, f'Mean face share: {original["mean_face_prompt_share"]:.3f} for originals and {mooney["mean_face_prompt_share"]:.3f} for Mooneys. Scores depend on the prompt set.',
         .65, 6.76, 12, .25, 12, color=MUTED)

    # 9–10. Actual screenshots, kept large enough to read.
    slide = page('Screenshot of the Mooney tool', 'The GUI displays the original, the binary output, and controls for white pixels and blur.')
    picture(slide, assets / 'tool_gui.png', .57, 1.78, 8.05, 5.18, name='Actual screenshot of running Mooney GUI')
    rect(slide, 8.91, 2.09, 3.84, 4.26, WHITE)
    text(slide, 'Controls', 9.14, 2.36, 3.36, .42, 22, True)
    text(slide, 'White pixels\nSet the target white proportion.\n\nGaussian blur\nSet the smoothing strength in pixels.\n\nBatch command\nA run with 101 inputs verified batch processing.',
         9.14, 3.02, 3.32, 3.04, 16)
    slide = page('Screenshot of the Mooney generation code',
                 'Actual excerpt from make_mooney() in mooney_tool.py.')
    picture(slide, assets / 'generator_excerpt.png', .59, 1.89, 12.13, 4.63,
            name='Actual generator source screenshot')
    text(slide, 'The wider blur resolves ties at the threshold so the selected white-pixel count stays exact.',
         .57, 6.64, 12.2, .29, 14, color=MUTED)

    # 11. Required disclosure, kept in one place.
    slide = page('Declaration of AI usage')
    rect(slide, .63, 1.88, 12.05, 3.65, WHITE)
    text(slide, 'ChatGPT / Codex', .91, 2.18, 11.45, .55, 25, True, TEAL)
    text(slide, 'I used ChatGPT/Codex to help interpret the brief, screen input images, develop and verify the code, run the models, analyze the outputs, and prepare the slides and ZIP.',
         .91, 3.03, 11.39, 1.07, 21)
    text(slide, 'I reviewed the suggested pairs and confirmed the ten shown on slide 3.', .91, 4.49, 11.35, .54, 20, True)
    text(slide, 'Hadis Nouri', .91, 5.88, 11.4, .45, 18, color=MUTED)

    # 12–13. Readable archive inventory and checklist with explicit slide numbers.
    slide = page('Submission ZIP contents', 'Open the ZIP to find these folders and the single PowerPoint at its root.')
    entries = [
        ('Original/', '100 original PNGs', '010.png'),
        ('Mooney/', '100 binary PNGs', '010.png'),
        ('Subset/Original/', '10 selected original PNGs', '010.png'),
        ('Subset/Mooney/', '10 selected Mooney PNGs', '010.png'),
        ('Result1/Original/', '100 depth PNGs + 100 preview JPEGs', '010_depth16.png'),
        ('Result1/Mooney/', '100 depth PNGs + 100 preview JPEGs', '010_depth_vis.jpg'),
        ('Result2/Original/', '100 CLIP JSONs', '010.json'),
        ('Result2/Mooney/', '100 CLIP JSONs', '010.json'),
        ('ZIP root', '1 PowerPoint', 'CompVP_Part1_Hadis_Nouri.pptx'),
    ]
    xs, ws = [.78, 4.02, 8.92], [3.07, 4.65, 3.71]
    rect(slide, .61, 1.92, 12.12, .49, NAVY)
    row(slide, ['Path', 'Contents', 'Example file'], xs, ws, 2.02, size=15, bold=True, color=WHITE)
    for idx, item in enumerate(entries):
        y = 2.43 + idx * .46
        rect(slide, .61, y, 12.12, .447, WHITE if idx % 2 == 0 else SOFT)
        row(slide, item, xs, ws, y + .10, size=14)
    text(slide, '821 files total. The same three-digit IDs link the inputs and model outputs.', .65, 6.72, 12, .27, 13, True, TEAL)
    slide = page('Part 1 deliverables checklist')
    required = [
        ('Title slide with all team member names', '1'),
        ('One-page description of the approach and idea', '2'),
        ('One slide with 10 originals and 10 Mooneys', '3'),
        ('Declaration of the vision systems used', '4'),
        ('Processing results for both vision systems', '5–8'),
        ('Screenshot showing the tool', '9'),
        ('Screenshot of the Mooney generation code', '10'),
        ('Declaration of AI usage', '11'),
        ('ZIP folder structure and file counts', '12'),
    ]
    for index, (label, number) in enumerate(required):
        y = 1.81 + index * .54
        rect(slide, .61, y, 12.10, .50, WHITE if index % 2 == 0 else SOFT)
        row(slide, [label, 'Slide ' + number], [.82, 10.91], [9.91, 1.65], y + .12, size=16)

    slide = page('Sources and references', 'Individual photograph credits and links are listed on the following slides.', section='APPENDIX')
    references = [
        ('FFHQ', 'NVIDIA Flickr-Faces-HQ dataset. The provided aligned photographs were used at 1024 × 1024.', 'https://github.com/NVlabs/ffhq-dataset'),
        ('Mooney method', 'Egger et al. Inverse Rendering Best Explains Face Perception Under Extreme Illuminations. Course reading.', None),
        ('Depth Anything V2 Small', 'Official Hugging Face checkpoint and processor.', 'https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf'),
        ('CLIP ViT-B/32', 'Official OpenAI checkpoint and processor.', 'https://huggingface.co/openai/clip-vit-base-patch32'),
        ('Kaggle run', 'Saved execution with both systems and the analysis outputs.', 'https://www.kaggle.com/code/mantra26/compvp-part1-high-resolution-rebuild'),
    ]
    for idx, (label, description, url) in enumerate(references):
        y = 1.95 + idx * .88
        text(slide, label, .65, y, 3.19, .50, 17, True, TEAL, url=url)
        text(slide, description, 3.94, y, 8.7, .60, 16)
    with (analysis / 'ATTRIBUTION.csv').open() as handle:
        credits = list(csv.DictReader(handle))
    for start in range(0, len(credits), 10):
        slide = page(f'FFHQ photo credits {start + 1:03}–{start + 10:03}',
                     'The photo and license links open the original sources. The Mooney images are derived from these photographs.',
                     section='APPENDIX')
        credit_x = [.70, 2.11, 5.97, 8.05]
        credit_w = [1.28, 3.67, 1.95, 4.55]
        row(slide, ['ID / FFHQ', 'Photographer / source', 'Photo', 'License'],
            credit_x, credit_w, 1.91, size=14, bold=True, color=TEAL)
        for idx, credit in enumerate(credits[start:start + 10]):
            y = 2.30 + idx * .43
            rect(slide, .61, y - .05, 12.12, .40, WHITE if idx % 2 == 0 else SOFT)
            author = credit['author']
            if len(author) > 44:
                author = author[:43] + '…'
            row(slide, [Path(credit['image']).stem + ' / ' + credit['ffhq_id'], author],
                credit_x[:2], credit_w[:2], y + .016, size=12)
            text(slide, 'Source photo', credit_x[2], y + .016, credit_w[2], .31, 12, color=TEAL, url=credit['photo_url'])
            text(slide, credit['license'], credit_x[3], y + .016, credit_w[3], .31, 12, color=TEAL, url=credit['license_url'])
        text(slide, 'The source archive includes the complete attribution table.', .65, 6.74, 12, .22, 11, color=MUTED)

    path = submission / 'CompVP_Part1_Hadis_Nouri.pptx'
    deck.save(path)
    return path


if __name__ == '__main__':
    print(main())
