from pymongo import MongoClient


class Mongo:
    def __init__(self):
        """Initialize our Mongo setup to store the payouts"""
        client = MongoClient()
        client = MongoClient('you-mongo-url')
        self.collection = client.mina.payouts
