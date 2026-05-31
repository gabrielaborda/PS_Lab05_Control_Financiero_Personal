from pytest_bdd import scenarios

from tests import bdd_steps  # noqa: F401

scenarios("../features/transacciones.feature")
