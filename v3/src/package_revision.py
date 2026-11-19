"""Replace the presentation in a verified Part 1 ZIP and verify all members."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import zipfile

PRESENTATION = 'CompVP_Part1_Hadis_Nouri.pptx'
FINAL_ARCHIVE = 'CompVP_Part1_Hadis_Nouri_Final.zip'


def sha256_file(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def expected_inventory(selected):
    ids = [f'{index:03}' for index in range(1, 101)]
    inventory = {PRESENTATION}
    for kind in ['Original', 'Mooney']:
        inventory.update(f'{kind}/{stem}.png' for stem in ids)
        inventory.update(f'Subset/{kind}/{stem}.png' for stem in selected)
        inventory.update(f'Result1/{kind}/{stem}{suffix}' for stem in ids
                         for suffix in ['_depth16.png', '_depth_vis.jpg'])
        inventory.update(f'Result2/{kind}/{stem}.json' for stem in ids)
    assert len(inventory) == 821
    return inventory


def package(base_archive, presentation, inventory_file, manual_file, output):
    selected = json.loads(manual_file.read_text())['ids']
    inventory = expected_inventory(selected)
    old_hashes = json.loads(inventory_file.read_text())
    assert set(old_hashes) == inventory
    slides = presentation.read_bytes()
    with zipfile.ZipFile(presentation) as deck:
        assert deck.testzip() is None
        assert 'ppt/slides/slide24.xml' in deck.namelist()
    observed = {}
    locations = Counter()
    destination = output.with_suffix('.partial')
    try:
        with zipfile.ZipFile(base_archive) as source, zipfile.ZipFile(
            destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=6
        ) as target:
            archive_files = [i.filename for i in source.infolist() if not i.is_dir()]
            assert len(archive_files) == len(inventory) and set(archive_files) == inventory
            for name in sorted(inventory):
                data = slides if name == PRESENTATION else source.read(name)
                digest = hashlib.sha256(data).hexdigest()
                if name != PRESENTATION:
                    record = old_hashes[name]
                    assert len(data) == record['bytes'] and digest == record['sha256'], name
                info = zipfile.ZipInfo(name, date_time=(2026, 11, 19, 0, 0, 0))
                target.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
                observed[name] = {'bytes': len(data), 'sha256': digest}
                locations[str(Path(name).parent)] += 1
        with zipfile.ZipFile(destination) as final:
            assert final.testzip() is None
            assert len(final.namelist()) == 821 and set(final.namelist()) == inventory
            for name, record in observed.items():
                assert hashlib.sha256(final.read(name)).hexdigest() == record['sha256'], name
            for kind in ['Original', 'Mooney']:
                for stem in selected:
                    basename = f'{kind}/{stem}.png'
                    assert final.read(basename) == final.read(f'Subset/{basename}')
        destination.replace(output)
    finally:
        destination.unlink(missing_ok=True)

    with output.open('rb') as handle:
        checksum_md5 = hashlib.file_digest(handle, 'md5').hexdigest()
    result = {
        'archive': output.name,
        'bytes': output.stat().st_size,
        'sha256': sha256_file(output),
        'md5': checksum_md5,
        'archive_crc': 'passed',
        'archive_sha256_per_member': 'passed',
        'data_files_matched_to_verified_Kaggle_archive': 820,
        'powerpoint_files_at_root': 1,
        'counts': dict(sorted(locations.items())),
        'manual_subset': selected,
    }
    output.with_name('archive_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ['base', 'presentation', 'inventory', 'manual', 'output']:
        parser.add_argument('--' + option, required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.base, args.presentation, args.inventory, args.manual, args.output), indent=2))
