# coding=utf-8
import json

import requests

from misc import get_config


def debugAccessToken(parameters):
    pass

def graphAPICall(url: str, parameters, debug: bool = True):
    data = requests.get(url, parameters)

    response = dict()
    response["url"] = url
    response["parameters"] = parameters
    response["parameters_pretty"] = json.dumps(parameters, indent=4, sort_keys=True)

    response["json_data"] = json.loads(data.content)
    response["json_data_pretty"] = json.dumps(response["json_data"], indent=4, sort_keys=True)

    return response


def main():
    config = get_config()
    endpoint_base = config["facebook_graph_domain"] + config["facebook_graph_version"] + "/"
    debug = False


if __name__ == "__main__":
    main()
