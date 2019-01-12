from collections.abc import MutableMapping
from copy import deepcopy

import torch

__all__ = ["Map", "TensorTuple"]


class Map(MutableMapping):
    __default_methods = ["update", "keys", "items", "values", "clear",
                         "copy", "get", "pop", "to", "deepcopy"] + __import__('keyword').kwlist
    __slots__ = ["_data"]

    def __init__(self, **kwargs):
        """
        dict like object but: stored values can be subscribed and attributed.
        >>> m = Map(test="test")
        >>> m.test is m["test"]
        Both of them are valid
        """
        super(Map, self).__init__()
        self._data = {}
        if len(kwargs) > 0:
            self._data.update(kwargs)

    def __getattr__(self, item):
        if item in self.__default_methods:
            return getattr(self, item)
        return self._data.get(item)

    def __setattr__(self, key, value):
        if key == "_data":
            # initialization!
            super(Map, self).__setattr__(key, value)
        elif key not in self.__default_methods:
            self._data[key] = value
        else:
            raise KeyError(f"{key} is a method name.")

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)

    def __len__(self):
        return len(self._data)

    def __delitem__(self, key):
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __repr__(self):
        _str = self.__class__.__name__ + "("
        for k, v in self._data.items():
            _str += f"{k}={str(v)}, "
        # to strip the las ", "
        return _str.strip(", ") + ")"

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def to(self, device: str, **kwargs):
        """move stored tensors to a given device
        """
        for k, v in self._data.items():
            if isinstance(v, torch.Tensor):
                self._data[k] = v.to(device, **kwargs)
        return self

    def deepcopy(self):
        new = Map()
        for k, v in self._data.items():
            if isinstance(v, torch.Tensor):
                # Only leave tensors support __deepcopy__
                new[k] = v.detach()
            else:
                new[k] = deepcopy(v)
        return new

    def copy(self):
        new = Map()
        new._data = self._data.copy()
        return new


class TensorTuple(tuple):

    def to(self, *args, **kwargs):
        return TensorTuple((t.to(*args, **kwargs) for t in self))


class StepDict(dict):
    def __init__(self, _type, **kwargs):
        super(StepDict, self).__init__(**kwargs)
        for k, v in self.items():
            if not (v is None and isinstance(v, _type)):
                raise RuntimeError(f"Expected Optimizer as values but got {type(v)} with key ({k})")

    def step(self):
        for v in self.values():
            if v is not None:
                v.step()

    def state_dict(self):
        d = {}
        for k, v in self.items():
            if v is not None:
                d[k] = v.stated_dict()
        return d

    def load_state_dict(self, state_dict: dict):
        for k, v in state_dict.items():
            if v is not None:
                self[k].load_state_dict(v)
