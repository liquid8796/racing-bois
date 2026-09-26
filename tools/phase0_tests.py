"""Synthetic fixtures only; no bundled original game data or fonts."""
import struct,unittest
from research_formats import FormatError,resources,sprites,encode_sprites,course_sections,midi_structure,riff_chunks,sfnt_structure,decode_family
from decode_reference_assets import explode_binary
from native_oracle import signed,div,port_spec

class ParserTests(unittest.TestCase):
    def test_dat_roundtrip(self):
        data=b'\x02\x02abcd\x00\x00\x01\x02xy';self.assertEqual(encode_sprites(sprites(data)),data);self.assertEqual(len(sprites(data)),3)
    def test_dat_truncation(self):
        for data in [b'\x01',b'\x02\x02abc']:
            with self.subTest(data=data),self.assertRaises(FormatError):sprites(data)
    def test_rsrc_magic(self):
        with self.assertRaises(FormatError):resources(bytes(64))
    def test_rsrc_bad_table(self):
        with self.assertRaises(FormatError):resources(b'CRSR'+bytes(12)+struct.pack('<I',99999)+bytes(20))
    def test_sgs_length(self):
        with self.assertRaises(FormatError):course_sections(b'SGSR'+struct.pack('<III',500,0,336))
    def test_sgs_count(self):
        with self.assertRaises(FormatError):course_sections(b'SGSR'+struct.pack('<III',16,100000,336))
    def test_riff_empty(self):self.assertEqual(riff_chunks(b'RIFF'+struct.pack('<I',4)+b'WAVE')['form'],'WAVE')
    def test_riff_bounds(self):
        with self.assertRaises(FormatError):riff_chunks(b'RIFF'+struct.pack('<I',100)+b'WAVE')
    def test_midi_empty_track(self):self.assertEqual(midi_structure(b'MThd'+struct.pack('>IHHH',6,0,1,96)+b'MTrk'+struct.pack('>I',0))['tracks'],1)
    def test_midi_count(self):
        with self.assertRaises(FormatError):midi_structure(b'MThd'+struct.pack('>IHHH',6,0,1,96))
    def test_font_bounds(self):
        with self.assertRaises(FormatError):sfnt_structure(b'\x00\x01\x00\x00'+struct.pack('>H',40)+bytes(6))
    def test_dcl_vector(self):
        expected=b'AIAIAIAIAIAIA'
        body,count=explode_binary(bytes.fromhex('00048224258f807f'),len(expected));self.assertEqual(body,expected);self.assertEqual(count,8)
    def test_dcl_limit(self):
        with self.assertRaises(ValueError):explode_binary(bytes.fromhex('00048224258f807f'),11)
    def test_dcl_truncated(self):
        for stop in range(8):
            with self.subTest(stop=stop),self.assertRaises(ValueError):explode_binary(bytes.fromhex('00048224258f807f')[:stop],12)
    def test_family_stored(self):self.assertTrue(decode_family(struct.pack('<4I',8,8,0,0)+struct.pack('<II',0,8))[1]['placeholder'])
    def test_family_size(self):
        with self.assertRaises(FormatError):decode_family(struct.pack('<4I',2**31,0,0,0))
    def test_family_trailing(self):
        blob=bytes.fromhex('00048224258f807f')+b'x'
        with self.assertRaises(FormatError):decode_family(struct.pack('<4I',13,len(blob),0,1)+blob)
    def test_signed_division(self):self.assertEqual(div(-7,4),-1);self.assertEqual(signed(0xffffffff),-1)
    def test_divide_zero(self):
        with self.assertRaises(ValueError):div(10,0)
    def test_spec_length(self):
        with self.assertRaises(ValueError):port_spec(bytes(355),75)

from pathlib import Path
from research_formats import legacy_checksum, save_envelope, family_tree
from mids_reference import mids_events
from validate_phase0 import validate_paths, ROOT


def fake_container(descriptors):
    data=bytearray(256)
    data[:4]=b'CRSR'
    struct.pack_into('<I',data,16,32)
    data[32:36]=b'LBTR'
    struct.pack_into('<I',data,40,len(descriptors))
    for i,(rid,off,size) in enumerate(descriptors):
        struct.pack_into('<4sIII',data,48+32*i,b'CEPS',rid,off,size)
    return bytes(data)


def fake_mids(events, flags=0):
    fmt=struct.pack('<3I',96,4096,flags)
    body=struct.pack('<3I',1,0,len(events))+events
    content=b'MIDS'+b'fmt '+struct.pack('<I',len(fmt))+fmt+b'data'+struct.pack('<I',len(body))+body
    return b'RIFF'+struct.pack('<I',len(content))+content


class ConformanceRegressionTests(unittest.TestCase):
    def test_rsrc_valid_single(self):
        entry=resources(fake_container([(1,128,4)]))[0]
        self.assertEqual((entry.id,entry.offset,entry.size,entry.tag),(1,128,4,'SPEC'))
    def test_rsrc_past_end(self):
        with self.assertRaises(FormatError):resources(fake_container([(1,254,4)]))
    def test_rsrc_duplicate_identity(self):
        with self.assertRaises(FormatError):resources(fake_container([(1,128,4),(1,132,4)]))
    def test_rsrc_overlapping_payloads(self):
        with self.assertRaises(FormatError):resources(fake_container([(1,128,12),(2,132,4)]))
    def test_rsrc_table_overlap(self):
        with self.assertRaises(FormatError):resources(fake_container([(1,72,4)]))
    def test_mids_short_event(self):
        result=mids_events(fake_mids(struct.pack('<3I',5,0,0x007f3c90)))
        self.assertEqual(result['events'][0]['tick'],5)
        self.assertEqual(result['events'][0]['parameter'],0x7f3c90)
    def test_mids_no_stream_id(self):
        result=mids_events(fake_mids(struct.pack('<2I',12,0x0107a120),1))
        self.assertEqual(result['events'][0]['kind'],1)
        self.assertEqual(result['events'][0]['parameter'],500000)
    def test_mids_long_event_padding(self):
        result=mids_events(fake_mids(struct.pack('<3I',0,0,0x80000003)+b'abc'+bytes(1)))
        self.assertEqual(result['events'][0]['payload_hex'],'616263')
    def test_mids_long_event_truncated(self):
        with self.assertRaises(FormatError):mids_events(fake_mids(struct.pack('<3I',0,0,0x80000010)+b'abcd'))
    def test_mids_unsupported_flags(self):
        with self.assertRaises(FormatError):mids_events(fake_mids(bytes(12),2))
    def test_mids_buffer_overflow(self):
        data=bytearray(fake_mids(bytes(12)));struct.pack_into('<I',data,48,99999)
        with self.assertRaises(FormatError):mids_events(bytes(data))
    def test_checksum_empty(self):self.assertEqual(legacy_checksum(b''),0)
    def test_checksum_single(self):self.assertEqual(legacy_checksum(b'a'),0x00610000)
    def test_save_valid_synthetic(self):
        body=bytes.fromhex('addefeca')+bytes(152)
        result=save_envelope(struct.pack('<I',legacy_checksum(body))+body)
        self.assertEqual(result['checksum'],legacy_checksum(body)); self.assertEqual(result['record_count'],10)
    def test_all_zero_checksum_is_not_save_authentication(self):
        self.assertEqual(legacy_checksum(bytes(156)),0)
        with self.assertRaises(FormatError):save_envelope(bytes(160))
    def test_save_wrong_magic_with_correct_checksum(self):
        body=bytes(156)
        with self.assertRaises(FormatError):save_envelope(struct.pack('<I',legacy_checksum(body))+body)
    def test_save_corruption_rejected(self):
        body=bytes.fromhex('addefeca')+bytes(152)
        data=bytearray(struct.pack('<I',legacy_checksum(body))+body);data[21]^=1
        with self.assertRaises(FormatError):save_envelope(bytes(data))
    def test_output_outside_workspace_rejected(self):
        with self.assertRaises(ValueError):validate_paths(ROOT,ROOT.parent/'bad-output')
    def test_source_reference_output_overlap_rejected(self):
        with self.assertRaises(ValueError):validate_paths(ROOT,ROOT/'docs/research/evidence/test')
    def test_family_empty_header(self):self.assertEqual(family_tree(struct.pack('<II',0,8))['kind'],'empty')
    def test_negative_integer_division(self):
        for a,b,expected in [(-7,3,-2),(7,-3,-2),(-7,-3,2),(-1,4,0)]:
            self.assertEqual(div(a,b),expected)
    def test_integer_division_overflow(self):
        with self.assertRaises(ValueError):div(-2147483648,-1)


if __name__=='__main__':unittest.main(verbosity=2)
