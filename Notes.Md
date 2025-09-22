# Firestore Structure Basics

## Firestore is NoSQL → data is stored in:

* Collection → like a table

* Document → like a row (JSON object)

* Sub-collection → nested collection under a document

* Example structure for chat history:

```scss
chat-history-storage (collection)
   └── session_id (document)
        └── messages (sub-collection)
             ├── msg1 (document)
             ├── msg2 (document)
