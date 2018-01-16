import io
import json
import numpy as np
import cadnano.fileio.v2encode as v2encode
import cadnano.fileio.v3encode as v3encode


def encodeToFile(filename, document, legacy=False):
    """
    Encodes the document as json object and outputs to file.

    Args:
        filename (str): Filename path for writing
        document (Document): Document to encode
        legacy (bool): Export for use with legacy (pre v2.5) cadnano versions.
    """
    json_string = encode(document, legacy)
    with io.open(filename, 'w', encoding='utf-8') as fd:
        fd.write(json_string)
# end def


def encode(document, legacy=False):
    """
    Encodes the document as json object.

    Args:
        document (Document): Document to encode
        legacy (bool): Export for use with legacy (pre v2.5) cadnano versions.

    Returns:
        str: the json string containing the encoded document
    """
    if legacy:
        obj = v2encode.encodeDocument(document)
    else:
        obj = v3encode.encodeDocument(document)
    json_string = json.dumps(obj, separators=(',', ':'), cls=EncoderforPandas)  # compact encoding
    return json_string


class EncoderforPandas(json.JSONEncoder):
    """
    Special encoder to coerce numpy number types into python types.
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
            except Exception:
                print(type(obj))
                raise
# end class
