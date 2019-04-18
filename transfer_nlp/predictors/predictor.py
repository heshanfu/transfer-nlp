from typing import Dict

import torch

from transfer_nlp.loaders.loaders import CustomDataset
from transfer_nlp.plugins.registry import Model, Data


class Predictor:

    PREDICTOR_CLASSES: {}

    def __init__(self, model: Model, data_loader: CustomDataset):
        self.model: Model = model
        self.model.eval()
        self.data_loader: CustomDataset = data_loader

    def json_to_data(self, input_json: Dict):
        """
        Transform a json entry into a data exemple
        :param input_json:
        :return:
        """
        raise NotImplementedError

    def output_to_json(self, *args, **kwargs):
        raise NotImplementedError

    def infer(self, *args, **kwargs):
        """
        Use the model to infer on some data example
        :param args:
        :param kwargs:
        :return:
        """
        with torch.no_grad():
            result = self.model(*args, **kwargs)
        return result

    def predict(self, *args, **kwargs):
        """
        Do inference and then decode the result
        :param args:
        :param kwargs:
        :return:
        """

        return self.model.decode(output=self.infer(args=args, kwargs=kwargs))

    def json_to_json(self, input_json: Dict):
        """
        Full prediction: input_json --> data example --> inference result --> decoded result --> json ouput
        :param input_json:
        :return:
        """

        return self.output_to_json(self.predict(self.json_to_data(input_json=input_json)))


    @classmethod
    def from_params(cls, config_args: Dict):
        model = Model.from_config(config_args=config_args)  # This should load the model object as well as pre-trained model weights
        data_loader = Data.from_config(config_args=config_args)  # Improve design of Data to be able to do this
        return cls(model=model, data_loader=data_loader)


def register_predictor(predictor_class):
    existing_classes = Predictor.PREDICTOR_CLASSES
    if predictor_class.__name__ in existing_classes:
        existing = list(existing_classes.keys())
        raise ValueError(f"{predictor_class.__name__} is already registered. Please have a look at the existing predictors: {existing}")
    else:
        existing_classes[predictor_class.__name__] = predictor_class
        return predictor_class


@register_predictor
class MyPredictor(Predictor):

    def __init__(self, model: Model, data_loader: CustomDataset):
        super().__init__(model=model, data_loader=data_loader)

    def json_to_data(self, input_example: Dict):





