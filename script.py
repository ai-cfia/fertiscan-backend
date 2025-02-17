from app.models.label_data import LabelData

data = """{
  "organizations": [],
  "cautions_en": [
    "string"
  ],
  "instructions_en": [],
  "cautions_fr": [
    "string"
  ],
  "ingredients_en": [],
  "instructions_fr": [],
  "density": {
    "value": 0,
    "unit": "string"
  },
  "fertiliser_name": "string",
  "guaranteed_analysis_en": {
    "title": "string",
    "nutrients": [],
    "is_minimal": true
  },
  "ingredients_fr": [],
  "npk": "8018709822834462374979581873055916014385267781453300108338394764319710753055465062114600833442499491.84587165866500347180567255330138041-183517764014516780379670856269939804880055366043288206850199765351142494725519897810.869132010771273419970474614863387945314-06379618211114288527854009396737834",
  "guaranteed_analysis_fr": {
    "title": "string",
    "nutrients": [],
    "is_minimal": true
  },
  "registration_number": [],
  "lot_number": "string",
  "weight": [],
  "volume": {
    "value": 0,
    "unit": "string"
  }
}"""


data = LabelData.model_validate_json(data)


print(data)
