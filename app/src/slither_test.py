import inspect
import json

from slither import Slither
from slither.detectors import all_detectors
from slither.detectors.abstract_detector import AbstractDetector


def load_by_address(address):
    sl = Slither(address)
    # print(sl.source_code)
    return sl

def save_detectors_info_to_json(sl: Slither):
    detectors = [getattr(all_detectors, name) for name in dir(all_detectors)]
    detectors = [d for d in detectors if inspect.isclass(d) and issubclass(d, AbstractDetector)]
    dectors_objs = [ _get_detector_dict(d) for d in detectors]

    print(dectors_objs)

    with open('detectors.json', 'w') as f:
        json.dump(dectors_objs, f)
    
    print('Detectors info saved to detectors.json')

def _get_detector_dict(detector) -> dict:
    return {
        #"key": detector.KEY,
        "argument": str(detector.ARGUMENT),
        "help": str(detector.HELP),
        "impact": str(detector.IMPACT),
        "confidence": str(detector.CONFIDENCE),
        "wiki": str(detector.WIKI),
        "wiki_title": str(detector.WIKI_TITLE),
        "wiki_description": str(detector.WIKI_DESCRIPTION),
        "wiki_exploit_scenario": str(detector.WIKI_EXPLOIT_SCENARIO),
        "wiki_recommendation": str(detector.WIKI_RECOMMENDATION)
    }

def describe_contracts(compilation_unit):
    # convert to JSON
    obj = {}
    for contract in compilation_unit.contracts:
        # Print the contract's name
        print(f'Contract: {contract.name}')
        obj.contract = {}
        # Print the name of the contract inherited
        print(f'\tInherit from{[c.name for c in contract.inheritance]}')
        for function in contract.functions:
            # For each function, print basic information
            print(f'\t{function.full_name}:')
            print(f'\t\tVisibility: {function.visibility}')
            print(f'\t\tContract: {function.contract}')
            print(f'\t\tModifier: {[m.name for m in function.modifiers]}')
            print(f'\t\tIs constructor? {function.is_constructor}')

# Load the compilation unit from the USDT address
# compilation_unit = load_by_address('0xdac17f958d2ee523a2206206994597c13d831ec7')
slither = load_by_address('0xdac17f958d2ee523a2206206994597c13d831ec7')

# detector_names = [d.ARGUMENT for d in detectors if hasattr(d, 'ARGUMENT')]
# print(detector_names)

detectors = [getattr(all_detectors, name) for name in dir(all_detectors)]
detectors = [d for d in detectors if inspect.isclass(d) and issubclass(d, AbstractDetector)]
for detector in detectors:
    slither.register_detector(detector)

# slither.register_detector(detectors[0])

results = slither.run_detectors()
# slither.register_detector()
# results = slither.run_detectors()
print(results)

# save_detectors_info_to_json(slither)
# Print all the contracts from the USDT address
# print([str(c) for c in compilation_unit.contracts])
# Print the most derived contracts from the USDT address
# print([str(c) for c in compilation_unit.contracts_derived])

# Describe the contracts from the USDT address
# describe_contracts(compilation_unit)

# write_json(compilation_unit, 'usdt.json')
