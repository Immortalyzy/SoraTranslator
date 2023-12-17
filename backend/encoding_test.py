""" debug encoding_fix.py  """
import Integrators.Chaos_R.Extractor.encoding_fix as enc_fix

# test the from_file_list method
python_file = "D:\\Work\\SoraTranslator\\GameResources\\OriginalFiles\\file_path.py"

# create an EncodingFix object from a python file, this will read files to unpack
encoding_fix = enc_fix.EncodingFix.from_pythonfile(python_file)

# print info
print(f"Read {len(encoding_fix.xp3_file_list)} files from {encoding_fix.directory}")

# test the unpacker
import Integrators.utils.utilities as util

print(util.XP3_UPK)

encoding_fix.set_unpacker(util.XP3_UPK)
encoding_fix.create_temp_unpack_directory()
encoding_fix.unpack_allfiles()

encoding_fix.original_encoding = "cp932"
encoding_fix.target_encoding = "utf_16"

encoding_fix.fix_allfiles()
encoding_fix.re_packallfiles()

# end debug
print("Done.")
