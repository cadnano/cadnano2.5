from os.path import basename
import numpy as np

from cadnano.cnenum import StrandType
import json
import io

# from cadnano.document import Document

import cadnano.fileio.v3encode as v3encode

def encodeToFile(filename, document):
    json_string = encode(document)
    with io.open(filename, 'w', encoding='utf-8') as fd:
        fd.write(json_string)
# end def

def encode(document):
    obj = v3encode.encodeDocument(document)
    json_string = json.dumps(obj, separators=(',', ':'), cls=EncoderforPandas)  # compact encoding
    return json_string

class EncoderforPandas(json.JSONEncoder):
    """ Special encoder to coerce numpy number types
    python types
    """
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        # if isinstance(obj, (np.integer):
        #     return int(obj)
        # elif isinstance(obj, np.floating):
        #     return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            try:
                return super(EncoderforPandas, self).default(obj)
            except:
                print(type(obj))
                raise
# end class