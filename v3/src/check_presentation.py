"""Verify the visible sections and the ability to edit and reopen the PowerPoint."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import zipfile

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

SECTIONS = [
    'Mooney Faces', 'Approach and idea', 'Ten selected originals and ten Mooneys',
    'Vision systems used', 'Result1 · Depth Anything outputs',
    'Result1 · Depth agreement across 100 pairs', 'Result2 · CLIP outputs',
    'Result2 · Face prompts across 200 images', 'Screenshot of the Mooney tool',
    'Screenshot of the Mooney generation code', 'Declaration of AI usage',
    'Submission ZIP contents', 'Part 1 deliverables checklist', 'Sources and references'
]


def validate(path, selected):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        xml = archive.read('ppt/presentation.xml')
        assert b'modifyVerifier' not in xml
    presentation = Presentation(path)
    assert len(presentation.slides) == 24
    texts = ['\n'.join(shape.text for shape in slide.shapes if shape.has_text_frame)
             for slide in presentation.slides]
    for index, title in enumerate(SECTIONS):
        assert title in texts[index], (index + 1, title)
    assert 'Hadis Nouri' in texts[0] and 'ChatGPT / Codex' in texts[10]
    for title in ['Depth Anything V2 Small', 'CLIP ViT-B/32', 'Result1', 'Result2']:
        assert title in texts[3]
    for directory in ['Original/', 'Mooney/', 'Subset/Original/', 'Subset/Mooney/',
                      'Result1/Original/', 'Result1/Mooney/', 'Result2/Original/', 'Result2/Mooney/']:
        assert directory in texts[11]
    subset_names = [shape.name for shape in presentation.slides[2].shapes
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE]
    assert len(subset_names) == 20
    assert set(subset_names) == {f'Subset/{kind}/{stem}.png' for kind in ['Original', 'Mooney'] for stem in selected}
    for index, title in [(8, 'Actual screenshot of running Mooney GUI'), (9, 'Actual generator source screenshot')]:
        assert any(shape.shape_type == MSO_SHAPE_TYPE.PICTURE and shape.name == title
                   for shape in presentation.slides[index].shapes)
    for slide in presentation.slides:
        for shape in slide.shapes:
            assert shape.left >= 0 and shape.top >= 0
            assert shape.left + shape.width <= presentation.slide_width
            assert shape.top + shape.height <= presentation.slide_height

    with TemporaryDirectory() as tmp:
        copy = Path(tmp) / 'edited.pptx'
        textbox = next(shape for shape in presentation.slides[0].shapes
                       if shape.has_text_frame and shape.text == 'Mooney Faces')
        textbox.text_frame.paragraphs[0].runs[0].text = 'Editable title check'
        presentation.save(copy)
        reopened = Presentation(copy)
        assert any(shape.has_text_frame and shape.text == 'Editable title check'
                   for shape in reopened.slides[0].shapes)
    return {'slides': len(texts), 'slide_titles_checked': SECTIONS, 'subset_images': 20,
            'edit_save_reopen_check_on_copy': 'passed',
            'presentation_package_crc': 'passed'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('presentation', type=Path)
    parser.add_argument('manual', type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.presentation, json.loads(args.manual.read_text())['ids']), indent=2))
