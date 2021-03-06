import copy
import unittest
from pathlib import Path

import ignite

from transfer_nlp.plugins.config import ExperimentConfig
from transfer_nlp.plugins.regularizers import L1
from transfer_nlp.plugins.trainers import BasicTrainer
from .trainer_utils import *

EXPERIMENT = {
    "my_dataset_splits": {
        "_name": "TestDataset",
        "data_file": Path(__file__).parent.resolve() / "sample_data.csv",
        "batch_size": 128,
        "vectorizer": {
            "_name": "TestVectorizer",
            "data_file": Path(__file__).parent.resolve() / "sample_data.csv"
        }
    },
    "model": {
        "_name": "TestModel",
        "hidden_dim": 100,
        "data": "$my_dataset_splits"
    },
    "optimizer": {
        "_name": "Adam",
        "lr": 0.01,
        "params": {
            "_name": "TrainableParameters"
        }
    },
    "scheduler": {
        "_name": "ReduceLROnPlateau",
        "patience": 1,
        "mode": "min",
        "factor": 0.5
    },
    "trainer": {
        "_name": "BasicTrainer",
        "model": "$model",
        "dataset_splits": "$my_dataset_splits",
        "loss": {
            "_name": "CrossEntropyLoss"
        },
        "optimizer": "$optimizer",
        "gradient_clipping": 0.25,
        "num_epochs": 5,
        "seed": 1337,
        "regularizer": {
            "_name": "L1"
        },
        "metrics": {
            "accuracy": {
                "_name": "Accuracy"
            },
            "loss": {
                "_name": "LossMetric",
                "loss_fn": {
                    "_name": "CrossEntropyLoss"
                }
            }
        },
        "finetune": False
    }

}


class RegistryTest(unittest.TestCase):

    def test_config(self):
        e = copy.deepcopy(EXPERIMENT)
        e = ExperimentConfig(e)
        trainer = e.experiment['trainer']

        self.assertIsInstance(trainer.model, TestModel)
        self.assertIsInstance(trainer.dataset_splits, TestDataset)
        self.assertIsInstance(trainer.loss, torch.nn.modules.loss.CrossEntropyLoss)
        self.assertIsInstance(trainer.optimizer, torch.optim.Adam)
        self.assertEqual(len(trainer.metrics), 2)
        self.assertEqual(trainer.device, torch.device(type='cpu'))
        self.assertEqual(trainer.seed, 1337)
        self.assertEqual(trainer.loss_accumulation_steps, 4)
        self.assertIsInstance(trainer.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau)
        self.assertEqual(trainer.num_epochs, 5)
        self.assertIsInstance(trainer.regularizer, L1)
        self.assertEqual(trainer.gradient_clipping, 0.25)
        self.assertEqual(trainer.finetune, False)
        self.assertEqual(trainer.embeddings_name, None)
        self.assertEqual(trainer.forward_params, ['x_in', 'apply_softmax'])
        # trainer.train()

        # Test factories
        optimizer = trainer.experiment_config.factories['optimizer'].create()
        self.assertIsInstance(optimizer, torch.optim.Adam)

        trainer = trainer.experiment_config.factories['trainer'].create()
        self.assertIsInstance(trainer, BasicTrainer)

    def test_setup(self):
        e = copy.deepcopy(EXPERIMENT)
        e = ExperimentConfig(e)
        trainer = e.experiment['trainer']
        trainer.setup(training_metrics=trainer.training_metrics)

        self.assertEqual(len(trainer.trainer._event_handlers[ignite.engine.Events.EPOCH_COMPLETED]), 5)
        self.assertEqual(len(trainer.trainer._event_handlers[ignite.engine.Events.ITERATION_COMPLETED]), 11)
        self.assertEqual(len(trainer.trainer._event_handlers[ignite.engine.Events.COMPLETED]), 2)
        self.assertEqual(len(trainer.trainer._event_handlers[ignite.engine.Events.STARTED]), 0)
        self.assertEqual(len(trainer.trainer._event_handlers[ignite.engine.Events.EPOCH_STARTED]), 5)
        self.assertEqual(len(trainer.trainer._event_handlers[ignite.engine.Events.ITERATION_STARTED]), 0)

    def test_forward(self):
        e = copy.deepcopy(EXPERIMENT)
        e = ExperimentConfig(e)
        trainer = e.experiment['trainer']
        trainer.setup(training_metrics=trainer.training_metrics)

        batch = next(iter(trainer.dataset_splits.train_data_loader()))
        self.assertEqual(list(batch.keys()), ['x_in', 'y_target'])
        output = trainer._forward(batch=batch)
        self.assertEqual(output.size()[0], min(len(trainer.dataset_splits.train_set), 128))
        self.assertEqual(output.size()[1], trainer.model.output_dim)
