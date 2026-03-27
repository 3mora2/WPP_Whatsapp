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
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ name, image, description, price, isHidden, url, retailerId, currency }) => {
                return WPP.commerce.createProduct({
                    name, image, description, price, isHidden, url, retailerId, currency
                });
            }""",
            {"name": name, "image": image, "description": description, "price": price,
             "isHidden": isHidden, "url": url, "retailerId": retailerId, "currency": currency},
            page=self.page
        )

    async def delProducts_(self, productsId: List[str]):
        """Delete products - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ productsId }) => {
                return WPP.commerce.removeProducts(productsId);
            }""",
            {"productsId": productsId},
            page=self.page
        )

    async def getProducts_(self, id: str, qnt: int):
        """Get products - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ id, qnt }) => {
                return WPP.commerce.getProducts({ id, qnt });
            }""",
            {"id": id, "qnt": qnt},
            page=self.page
        )

    async def getProductById_(self, id: str, productId: str):
        """Get product by ID - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ id, productId }) => {
                return WPP.commerce.getProductById(productId);
            }""",
            {"id": id, "productId": productId},
            page=self.page
        )

    async def getCollections_(self, id: str, qnt: str, maxProducts: str):
        """Get collections - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ id, qnt, maxProducts }) => {
                return WPP.commerce.getCollections({ id, qnt, maxProducts });
            }""",
            {"id": id, "qnt": qnt, "maxProducts": maxProducts},
            page=self.page
        )

    async def createCollection_(self, collectionName: str, productsId: List[str]):
        """Create collection - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ collectionName, productsId }) => {
                return WPP.commerce.createCollection(collectionName, productsId);
            }""",
            {"collectionName": collectionName, "productsId": productsId},
            page=self.page
        )

    async def deleteCollection_(self, collectionId: str):
        """Delete collection - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ collectionId }) => {
                return WPP.commerce.deleteCollection(collectionId);
            }""",
            {"collectionId": collectionId},
            page=self.page
        )

    async def editCollection_(self, collectionId: str, options: CollectionOptions):
        """Edit collection - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ collectionId, options }) => {
                return WPP.commerce.editCollection(collectionId, options);
            }""",
            {"collectionId": collectionId, "options": options},
            page=self.page
        )

    async def editProduct_(self, productId: str, options: ProductOptions):
        """Edit product - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ productId, options }) => {
                return WPP.commerce.editProduct(productId, options);
            }""",
            {"productId": productId, "options": options},
            page=self.page
        )

    async def addProductImage_(self, productId: str, image: str):
        """Add product image - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ productId, image }) => {
                return WPP.commerce.addProductImage(productId, image);
            }""",
            {"productId": productId, "image": image},
            page=self.page
        )

    async def changeProductImage_(self, productId: str, image: str):
        """Change product image - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ productId, image }) => {
                return WPP.commerce.changeProductImage(productId, image);
            }""",
            {"productId": productId, "image": image},
            page=self.page
        )

    async def getBusinessProfilesProducts_(self, id_: str):
        """Get business profile products - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ id }) => {
                return WPP.commerce.getProfileProducts(id);
            }""",
            {"id": id_},
            page=self.page
        )

    async def getOrderbyMsg_(self, messageId: str):
        """Get order by message - async implementation"""
        return await self.ThreadsafeBrowser.page_evaluate(
            """({ messageId }) => {
                return WPP.order.get(messageId);
            }""",
            {"messageId": messageId},
            page=self.page
        )
