apiurl|/api/behaviors/preview
description|Use SSML  to speak-Example:<speak></speak>
json|{"behaviorId": "PREVIEW", "sequenceJson": {"@type": "com.amazon.alexa.behaviors.model.Sequence", "startNode": {"operationPayload": {"customerId": "<deviceOwnerCustomerId>", "content": [{"display": {"title": "smartHomeNG", "body": "<mValue>"}, "speak": {"type": "text", "value": "<mValue>"}, "locale": "de-DE"}], "expireAfter": "PT5S", "target": {"customerId": "<deviceOwnerCustomerId>"}}, "type": "AlexaAnnouncement", "@type": "com.amazon.alexa.behaviors.model.OpaquePayloadOperationNode"}}, "status": "ENABLED"}
myReqType|POST
