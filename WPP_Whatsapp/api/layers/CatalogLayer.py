from __future__ import annotations

from typing import List, Optional
from WPP_Whatsapp.api.layers.HostLayer import HostLayer
from WPP_Whatsapp.api.model import CollectionOptions, ProductOptions


class CatalogLayer(HostLayer):
    """Layer for managing WhatsApp Business Catalog"""

    def createProduct(self,
                      name: str, image: str, description: str, price: float, isHidden: bool = False,
                      url: str = "", retailerId: str = "", currency: str = "USD", timeout=60):
        """
           * Create a product on catalog
           * @param name Product name
           * @param image Product image
           * @param description Product description
           * @param price Product price
           * @param isHidden Product visibility
           * @param url Product url
           * @param retailerId Product own ID system
           * @param currency Product currency
        """
        return self.ThreadsafeBrowser.run_threadsafe(
            self.createProduct_, name, image, description, price, isHidden, url, retailerId, currency, timeout_=timeout)

    def delProducts(self, productsId: List[str], timeout=60):
        """Delete product(s) on catalog"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.delProducts_, productsId, timeout_=timeout)

    def getProducts(self, id: str, qnt: int, timeout=60):
        """Query all products"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getProducts_, id, qnt, timeout_=timeout)

    def getProductById(self, id: str, productId: str, timeout=60):
        """Get product by ID"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getProductById_, id, productId, timeout_=timeout)

    def getCollections(self, id: str, qnt: str, maxProducts: str, timeout=60):
        """Query all collections"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getCollections_, id, qnt, maxProducts, timeout_=timeout)

    def createCollection(self, collectionName: str, productsId: List[str], timeout=60):
        """Create new collection"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.createCollection_, collectionName, productsId, timeout_=timeout)

    def deleteCollection(self, collectionId: str, timeout=60):
        """Delete a collection"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.deleteCollection_, collectionId, timeout_=timeout)

    def editCollection(self, collectionId: str, options: CollectionOptions, timeout=60):
        """Edit a collection"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.editCollection_, collectionId, options, timeout_=timeout)

    def editProduct(self, productId: str, options: ProductOptions, timeout=60):
        """Edit product on catalog"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.editProduct_, productId, options, timeout_=timeout)

    def addProductImage(self, productId: str, image: str, timeout=60):
        """Add image on product"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.addProductImage_, productId, image, timeout_=timeout)

    def changeProductImage(self, productId: str, image: str, timeout=60):
        """Change main image of product"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.changeProductImage_, productId, image, timeout_=timeout)

    def getBusinessProfilesProducts(self, id_: str, timeout=60):
        """Query product catalog"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getBusinessProfilesProducts_, id_, timeout_=timeout)

    def getOrderbyMsg(self, messageId: str, timeout=60):
        """Query order catalog"""
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getOrderbyMsg_, messageId, timeout_=timeout)

    # ##########################################################################
    # Async implementations
    # ##########################################################################

    async def createProduct_(self, name: str, image: str, description: str, price: float,
                            isHidden: bool, url: str, retailerId: str, currency: str):
        """Create a product - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.createProduct_.0',
            {"name": name, "image": image, "description": description, "price": price,
             "isHidden": isHidden, "url": url, "retailerId": retailerId, "currency": currency},
            page=self.page
        )

    async def delProducts_(self, productsId: List[str]):
        """Delete products - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.delProducts_.0',
            {"productsId": productsId},
            page=self.page
        )

    async def getProducts_(self, id: str, qnt: int):
        """Get products - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.getProducts_.0',
            {"id": id, "qnt": qnt},
            page=self.page
        )

    async def getProductById_(self, id: str, productId: str):
        """Get product by ID - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.getProductById_.0',
            {"id": id, "productId": productId},
            page=self.page
        )

    async def getCollections_(self, id: str, qnt: str, maxProducts: str):
        """Get collections - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.getCollections_.0',
            {"id": id, "qnt": qnt, "maxProducts": maxProducts},
            page=self.page
        )

    async def createCollection_(self, collectionName: str, productsId: List[str]):
        """Create collection - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.createCollection_.0',
            {"collectionName": collectionName, "productsId": productsId},
            page=self.page
        )

    async def deleteCollection_(self, collectionId: str):
        """Delete collection - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.deleteCollection_.0',
            {"collectionId": collectionId},
            page=self.page
        )

    async def editCollection_(self, collectionId: str, options: CollectionOptions):
        """Edit collection - async implementation"""
        options = dict(options)
        for old, new in [('name', 'collectionName'), ('products', 'productsToAdd')]:
            if old in options and new not in options:
                options[new] = options.pop(old)
        return await self._evaluate_js(
            'CatalogLayer.editCollection_.0',
            {"collectionId": collectionId, "options": options},
            page=self.page
        )

    async def editProduct_(self, productId: str, options: ProductOptions):
        """Edit product - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.editProduct_.0',
            {"productId": productId, "options": options},
            page=self.page
        )

    async def addProductImage_(self, productId: str, image: str):
        """Add product image - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.addProductImage_.0',
            {"productId": productId, "image": image},
            page=self.page
        )

    async def changeProductImage_(self, productId: str, image: str):
        """Change product image - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.changeProductImage_.0',
            {"productId": productId, "image": image},
            page=self.page
        )

    async def getBusinessProfilesProducts_(self, id_: str):
        """Get business profile products - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.getBusinessProfilesProducts_.0',
            {"id": id_},
            page=self.page
        )

    async def getOrderbyMsg_(self, messageId: str):
        """Get order by message - async implementation"""
        return await self._evaluate_js(
            'CatalogLayer.getOrderbyMsg_.0',
            {"messageId": messageId},
            page=self.page
        )

    def removeProductImage(self, productId, index, timeout=60):
        """Remove an additional product image."""
        return self.ThreadsafeBrowser.run_threadsafe(self.removeProductImage_, productId, index, timeout_=timeout)

    async def removeProductImage_(self, productId, index):
        return await self._evaluate_js(
            'CatalogLayer.removeProductImage_.0', {"productId": productId, "index": index}, page=self.page)

    def setProductVisibility(self, productId, value, timeout=60):
        """Set product visibility."""
        return self.ThreadsafeBrowser.run_threadsafe(self.setProductVisibility_, productId, value, timeout_=timeout)

    async def setProductVisibility_(self, productId, value):
        return await self._evaluate_js(
            'CatalogLayer.setProductVisibility_.0', {"productId": productId, "value": value}, page=self.page)

    def updateCartEnabled(self, value, timeout=60):
        """Enable or disable the business cart."""
        return self.ThreadsafeBrowser.run_threadsafe(self.updateCartEnabled_, value, timeout_=timeout)

    async def updateCartEnabled_(self, value):
        return await self._evaluate_js(
            'CatalogLayer.updateCartEnabled_.0', {"value": value}, page=self.page)
