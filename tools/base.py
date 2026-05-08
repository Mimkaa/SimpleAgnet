from abc import ABC, abstractmethod

class Tool(ABC):
    name = "base"

    @abstractmethod
    def run(self, **kwargs):
        raise NotImplementedError
