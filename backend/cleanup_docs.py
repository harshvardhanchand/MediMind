from app.db.session import get_db
from app.models.document import Document
from app.models.extracted_data import ExtractedData

db = next(get_db())

# Get the most recent documents to clean up
recent_docs = db.query(Document).order_by(Document.upload_timestamp.desc()).limit(10).all()

print("Recent documents found:")
for doc in recent_docs:
    print(f"ID: {doc.document_id}, File: {doc.original_filename}, Status: {doc.processing_status}")

if recent_docs:
    print(f"\nDeleting {len(recent_docs)} documents...")
    
    # Delete extracted_data first (foreign key constraint)
    extracted_data_deleted = 0
    for doc in recent_docs:
        extracted = db.query(ExtractedData).filter(ExtractedData.document_id == doc.document_id).first()
        if extracted:
            db.delete(extracted)
            extracted_data_deleted += 1
    
    # Then delete documents
    docs_deleted = 0
    for doc in recent_docs:
        db.delete(doc)
        docs_deleted += 1
    
    db.commit()
    print(f'Deleted {extracted_data_deleted} extracted_data records and {docs_deleted} documents')
else:
    print("No documents to delete")

db.close() 