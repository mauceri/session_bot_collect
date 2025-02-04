from abc import ABC, abstractmethod

class IObserver(ABC):

    @abstractmethod
    def notify(self,  msg:str, to:str, attachments):
        pass

    @abstractmethod
    def prefix(self:str):
        pass


class IObservable(ABC):
    
    @abstractmethod
    def subscribe(self, observer: IObserver):
        pass

    @abstractmethod
    def unsubscribe(self, observer: IObserver):
        pass

    @abstractmethod
    def notify(self, message: str, to: str, attachments):
        pass


class IPlugin(ABC):
    def __init__(self, observable:IObservable, data_path:str="/data"):
        self.data_path = data_path
        self.__observable = observable
        

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
    