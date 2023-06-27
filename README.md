# WPP_Whatsapp

WPP_Whatsapp aim of exporting functions from WhatsApp Web to the python, which can be used to support the creation of
any interaction, such as customer service, media sending, intelligence recognition based on phrases artificial and many
other things, use your imagination         
WPP_Whatsapp: [WPPConnect](https://github.com/wppconnect-team/wppconnect) Converted to python, so Documentation is same

<p align="center">
  <a href="https://wppconnect.io/wppconnect/pages/getting-started/basic-functions.html">Basic Function</a> •
  <a href="https://wppconnect.io/wppconnect/">Documentation</a>
</p>

## Functions

|                                                            |   |
|------------------------------------------------------------|---|
| Automatic QR Refresh                                       | ✔ |
| Send **text, image, video, audio and docs**                | ✔ |
| Get **contacts, chats, groups, group members, Block List** | ✔ |
| Send contacts                                              | ✔ |
| Send stickers                                              | ✔ |
| Send stickers GIF                                          | ✔ |
| Multiple Sessions                                          | ✔ |
| Forward Messages                                           | ✔ |
| Receive message                                            | ✔ |
| insert user section                                        | ✔ |
| Send _location_                                            | ✔ |
| **and much more**                                          | ✔ |

See more at <a href="https://wppconnect.io/wppconnect/classes/Whatsapp.html">WhatsApp methods</a>

## Installation

`pip install WPP_Whatsapp`

## Getting Started

### Sync

```
from WPP_Whatsapp import Create


self = Create(session="test")
self.async_to_sync(self.start())
```

### Async

```
import asyncio
from WPP_Whatsapp import Create


async def main():
    self = Create(session="test")
    client = await self.start()

asyncio.run(main())
```

## Send Text

### Sync

```
from WPP_Whatsapp import Create


self = Create(session="test")
self.async_to_sync(self.start())

if self.state != 'CONNECTED':
    raise Exception(self.state)
# Pass Number with code of country, and message
result = self.async_to_sync(self.client.sendText("201016708170", "hello from wpp"))
print(result)
"""{'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}"""
self.async_to_sync(self.client.close())
```

### Async

```
import asyncio
from WPP_Whatsapp import Create


async def main():
    self = Create(session="test")
    # Pass Session Name to Save whatsapp session
    client = await self.start()
    if self.state != 'CONNECTED':
        raise Exception(self.state)
    # Pass Number with code of country, and message
    result = await client.sendText("201016708170", "hello from wpp")
    print(result)
    """{'id': 'true_**********@c.us_*************_out', 'ack': 3, 'sendMsgResult': {}}"""
    await client.close()


asyncio.run(main())
```

## Receive New Message

```
def new_message(message):
    print(message)

self.client.onMessage(new_message)
# wait new message
self.client.loop.run_forever()
```

output

```
 """
        {
        'id': 'false_**********@c.us_3EB0103CAE63ADF8D84EE9', 'rowId': None, 'serverId': None, 'body': 'message_body',
        'type': 'chat', 'subtype': None, 't': 1687856231, 'revokeTimestamp': None, 'notifyName': '***',
        'from': '******@c.us', 'to': '******@c.us', 'author': None, 'self': 'in', 'ack': 1, 'invis': None,
        'isNewMsg': True, 'star': False, 'kicKey': None, 'kicState': None, 'kicTimestampMs': None, 'kicNotified': False,
        'keepType': None, 'keptMessageKey': None, 'keptCount': None, 'recvFresh': True, 'caption': None,
        'interactiveAnnotations': None, 'contextInfo': None, 'clientUrl': None, 'loc': None, 'lat': None, 'lng': None,
        'isLive': None, 'accuracy': None, 'speed': None, 'degrees': None, 'comment': None, 'sequence': None,
        'shareDuration': None, 'finalLat': None, 'finalLng': None, 'finalAccuracy': None, 'finalThumbnail': None,
        'finalSpeed': None, 'finalDegrees': None, 'finalTimeOffset': None, 'deprecatedMms3Url': None,
        'directPath': None, 'mimetype': None, 'duration': None, 'filehash': None, 'encFilehash': None, 'size': None,
        'filename': None, 'streamingSidecar': None, 'mediaKey': None, 'mediaKeyTimestamp': None, 'pageCount': None,
        'isGif': None, 'gifAttribution': None, 'isViewOnce': None, 'streamable': None, 'width': None, 'height': None,
        'thumbnailDirectPath': None, 'thumbnailSha256': None, 'thumbnailEncSha256': None, 'thumbnailHeight': None,
        'thumbnailWidth': None, 'waveform': None, 'staticUrl': None, 'stickerPackId': None, 'stickerPackName': None,
        'stickerPackPublisher': None, 'mediaHandle': None, 'scanLengths': None, 'scansSidecar': None,
        'isFromTemplate': False, 'devicesAdded': None, 'devicesRemoved': None, 'isThisDeviceAdded': None,
        'firstFrameLength': None, 'firstFrameSidecar': None, 'isAnimated': None, 'canonicalUrl': None,
        'matchedText': None, 'thumbnail': '', 'thumbnailHQ': None, 'richPreviewType': None, 'doNotPlayInline': None,
        'rcat': None, 'title': None, 'description': None, 'businessOwnerJid': None, 'productId': None,
        'currencyCode': None, 'priceAmount1000': None, 'salePriceAmount1000': None, 'retailerId': None, 'url': None,
        'productImageCount': None, 'sessionId': None, 'pollName': None, 'pollOptions': None,
        'pollSelectableOptionsCount': None, 'pollInvalidated': False, 'isSentCagPollCreation': False,
        'pollUpdateParentKey': None, 'encPollVote': None, 'senderTimestampMs': None, 'latestEditMsgKey': None,
        'latestEditSenderTimestampMs': None, 'editMsgType': None, 'recipients': None, 'broadcast': False,
        'quotedMsg': None, 'quotedStanzaID': None, 'quotedRemoteJid': None, 'quotedParticipant': None,
        'quotedGroupSubject': None, 'quotedParentGroupJid': None, 'mentionedJidList': [], 'groupMentions': [],
        'footer': None, 'hydratedButtons': None, 'hsmTag': None, 'hsmCategory': None, 'selectedId': None,
        'selectedIndex': None, 'multicast': None, 'urlText': None, 'urlNumber': None, 'clearMedia': None,
        'isVcardOverMmsDocument': False, 'isCaptionByUser': None, 'vcardList': None, 'vcardFormattedName': None,
        'revokeSender': None, 'protocolMessageKey': None, 'futureproofBuffer': None, 'futureproofParams': None,
        'futureproofType': None, 'futureproofSubtype': None, 'templateParams': None, 'textColor': None,
        'backgroundColor': None, 'font': None, 'campaignId': None, 'campaignDuration': None, 'actionLink': None,
        'statusPSAReadTimestamp': None, 'isForwarded': None, 'forwardingScore': None, 'labels': [],
        'hasReaction': False, 'paymentCurrency': None, 'paymentAmount1000': None, 'paymentMessageReceiverJid': None,
        'paymentTransactionTimestamp': None, 'paymentStatus': None, 'paymentTxnStatus': None, 'paymentNoteMsg': None,
        'paymentRequestMessageKey': None, 'paymentExpiryTimestamp': None, 'paymentInviteServiceType': None,
        'paymentBackground': None, 'ephemeralStartTimestamp': None, 'ephemeralDuration': None,
        'ephemeralSettingTimestamp': 1687688096, 'ephemeralOutOfSync': None, 'ephemeralSharedSecret': None,
        'disappearingModeInitiator': 'chat', 'ephemeralSettingUser': None, 'messageSecret': None,
        'originalSelfAuthor': None, 'bizPrivacyStatus': None, 'privacyModeWhenSent': None, 'verifiedBizName': None,
        'inviteCode': None, 'inviteCodeExp': None, 'inviteGrp': None, 'inviteGrpName': None, 'inviteGrpJpegThum': None,
        'inviteGrpType': 'DEFAULT', 'sellerJid': None, 'message': None, 'orderTitle': None, 'itemCount': None,
        'orderId': None, 'surface': None, 'status': None, 'token': None, 'totalAmount1000': None,
        'totalCurrencyCode': None, 'historySyncMetaData': None, 'isSendFailure': None, 'errorCode': None,
        'appStateSyncKeyShare': None, 'appStateSyncKeyRequest': None, 'appStateFatalExceptionNotification': None,
        'peerDataOperationRequestMessage': None, 'peerDataOperationRequestResponseMessage': None,
        'broadcastParticipants': None, 'broadcastEphSettings': None, 'broadcastId': None, 'ctwaContext': None,
        'list': None, 'listResponse': None, 'productListItemCount': None, 'productHeaderImageRejected': False,
        'agentId': None, 'lastPlaybackProgress': 0, 'isDynamicReplyButtonsMsg': False, 'dynamicReplyButtons': None,
        'buttonsResponse': None, 'selectedButtonId': None, 'headerType': None, 'nativeFlowName': None,
        'nativeFlowButtons': None, 'interactiveHeader': None, 'interactiveType': None, 'interactivePayload': None,
        'reactionParentKey': None, 'reactionText': None, 'reactionTimestamp': None, 'encReactionTargetMessageKey': None,
        'encReactionEncIv': None, 'encReactionEncPayload': None, 'pinParentKey': None, 'pinMessageType': None,
        'pinSenderTimestampMs': None, 'pinExpiryDuration': None, 'isMdHistoryMsg': False, 'stickerSentTs': 0,
        'isAvatar': False, 'bizSource': None, 'requiresDirectConnection': False,
        'chatId': {'server': 'c.us', 'user': '*********', '_serialized': '*******@c.us'}, 'fromMe': False,
        'sender': {'id': {'server': 'c.us', 'user': '**********', '_serialized': '**********@c.us'},
                   'name': '**********', 'shortName': '', 'pushname': '**********', 'type': 'in',
                   'verifiedName': None, 'isBusiness': None, 'isEnterprise': None, 'isSmb': None, 'verifiedLevel': None,
                   'privacyMode': None, 'statusMute': None, 'sectionHeader': None, 'labels': [],
                   'isContactSyncCompleted': 1, 'forcedBusinessUpdateFromServer': None,
                   'disappearingModeDuration': None, 'disappearingModeSettingTimestamp': None,
                   'requestedPnTimestamp': None, 'formattedName': '010-289-46519', 'isHighLevelVerified': None,
                   'isMe': False, 'isMyContact': True, 'isPSA': False, 'isUser': True, 'isVerified': None,
                   'isWAContact': True, 'profilePicThumbObj': {
                'eurl': 'https://pps.whatsapp.net/v/**********',
                'id': {'server': 'c.us', 'user': '201028946519', '_serialized': '201028946519@c.us'},
                'img': 'https://pps.whatsapp.net/v/t61.24694-24/**********',
                'imgFull': 'https://pps.whatsapp.net/v/t61.24694-24/**********',
                'raw': None, 'tag': '1591201851'}, 'msgs': None}, 'timestamp': 1687856231, 'content': '.',
        'isGroupMsg': False, 'isLink': None, 'isMMS': None, 'isMedia': None, 'isNotification': None, 'isPSA': None,
        'quotedMsgId': None, 'mediaData': {}}
"""
```