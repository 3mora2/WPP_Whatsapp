from WPP_Whatsapp.api.layers.CatalogLayer import CatalogLayer


class LabelsLayer(CatalogLayer):
    def addNewLabel(self, name, options, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.addNewLabel_, name, options, timeout_=timeout)

    def addOrRemoveLabels(self, chatIds, options, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.addOrRemoveLabels_, chatIds, options, timeout_=timeout)

    def getAllLabels(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getAllLabels_, timeout_=timeout)

    def getLabelById(self, Id, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.getLabelById_, Id, timeout_=timeout)

    def deleteAllLabels(self, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.deleteAllLabels_, timeout_=timeout)

    def deleteLabel(self, Id, timeout=60):
        return self.ThreadsafeBrowser.run_threadsafe(
            self.deleteLabel_, Id, timeout_=timeout)

    ######################################
    async def addNewLabel_(self, name, options):
        """
          /**
           * Create New Label
           * @category Labels
           *
           * @example
           * ```javascript
           * client.addNewLabel(`Name of label`);
           * //or
           * client.addNewLabel(`Name of label`, { labelColor: '#dfaef0' });
           * //or
           * client.addNewLabel(`Name of label`, { labelColor: 4292849392 });
           * ```
           * @param name Name of label
           * @param options options of label
           */
        """
        return await self.ThreadsafeBrowser.page_evaluate("""({ name, options }) => {
        WPP.labels.addNewLabel(name, options);
      }""", {"name": name, "options": options}, page=self.page)

    async def addOrRemoveLabels_(self, chatIds, options):
        """
          /**
           * Add or delete label of chatId
           * @category Labels
           *
           * @example
           * ```javascript
           * client.addOrRemoveLabels(['[number]@c.us','[number]@c.us'],
           * [{labelId:'76', type:'add'},{labelId:'75', type:'remove'}]);
           * //or
           * ```
           * @param chatIds ChatIds
           * @param options options to remove or add
           */
        """
        return await self.ThreadsafeBrowser.page_evaluate("""({ chatIds, options }) => {
        WPP.labels.addOrRemoveLabels(chatIds, options);
      }""", {"chatIds": chatIds, "options": options}, page=self.page)

    async def getAllLabels_(self):
        return await self.ThreadsafeBrowser.page_evaluate("() => WPP.labels.getAllLabels()", page=self.page)

    async def getLabelById_(self, Id):
        return await self.ThreadsafeBrowser.page_evaluate("""({ id }) => {WPP.labels.getLabelById(id); }""", {"id": Id}, page=self.page)

    async def deleteAllLabels_(self):
        return await self.ThreadsafeBrowser.page_evaluate("""() => {WPP.labels.deleteAllLabels();}""", page=self.page)

    async def deleteLabel_(self, Id):
        return await self.ThreadsafeBrowser.page_evaluate("""({ id }) => {WPP.labels.deleteLabel(id); }""", {"id": Id}, page=self.page)
