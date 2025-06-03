**Components:**

1.  **Mobile App (Frontend):** User interface for all interactions.
2.  **Backend API:** Handles business logic, data processing orchestration, and communication between frontend, database, storage, and AI services.
3.  **Managed Relational Database:** Stores user accounts, structured extracted data, document metadata, and audit logs.
4.  **Secure Object Storage:** Stores the original uploaded documents (PDFs, images).
5.  **Cloud AI Services:** Provides managed services for OCR, medical NLP, and LLM-based query interpretation (**Gemini 2.5 Flash**).

## 3. Proposed Technology Choices

*(Note: These are specific proposals based on the PRD's guidelines and solo-dev context. Alternatives exist.)*

3. Technology Stack

* **Frontend Framework:** **React Native** (JavaScript/TypeScript) - Cross-platform, large community, suitable for solo dev.
* **UI Library (React Native):** **React Native Paper** or **NativeBase** - Provides pre-built components following Material Design or custom design systems.
* **State Management (React Native):** **Zustand** or **Redux Toolkit** - Choose based on complexity needs and developer preference (Zustand is simpler).
* **Backend Framework:** **Python 3.1x** with **FastAPI** - Modern, fast, async, good typing, auto-docs.
* **Database:** **Google Cloud SQL for PostgreSQL** (v15+) - Managed, scalable, supports compliance features. **Ensure deployment in a suitable region (e.g., `asia-south1` Mumbai) and review DPDP Act data localization needs.**
* **Object Storage:** **Google Cloud Storage (GCS)** - Standard Bucket, **Uniform Bucket-Level Access enabled**, configured in the same region as Cloud SQL.
* **Authentication:** **Firebase Authentication** - Managed service, integrates well with React Native via `react-native-firebase`.
* **OCR Service:** **Google Cloud Vision API** (`DOCUMENT_TEXT_DETECTION`).
* **Medical NLP Service:** **Google Cloud Healthcare Natural Language API** (`analyzeEntities` endpoint). Requires BAA for HIPAA adherence if targeting US users; check terms.
* **Query LLM Service:** **Google Cloud Vertex AI Gemini 2.5 Flash API** - Use appropriate regional endpoint and review terms regarding data processing/compliance.
* **Medical AI Services:** **Google Gemini Pro API** for medical reasoning, **BioBERT** (`dmis-lab/biobert-v1.1`) for medical embeddings, **pgvector** for vector similarity search.
* **Vector Database:** **pgvector** extension for PostgreSQL - Fast vector similarity search with HNSW indexing.
* **ML Libraries:** **transformers**, **torch**, **sentence-transformers**, **scikit-learn**, **numpy** for AI/ML processing.
* **Deployment (Backend):** **Google Cloud Run** - Serverless container platform, scales to zero, simple deployment.
* **Task Queue:** **Google Cloud Tasks** - For reliable asynchronous task execution.
* **Cloud Platform:** **Google Cloud Platform (GCP)**

## 4. Data Model / Database Schema

*(Simplified - Primary Tables & Key Fields)*

* **`users`**
    * `user_id` (Primary Key, UUID)
    * `auth_provider_id` (e.g., ID from Firebase Auth/Cognito/Auth0, unique)
    * `email` (Indexed, potentially encrypted)
    * `created_at` (Timestamp)
    * `updated_at` (Timestamp)

* **`documents`**
    * `document_id` (Primary Key, UUID)
    * `user_id` (Foreign Key to `users`, Indexed)
    * `original_filename` (Text)
    * `storage_path` (Text - path in secure object storage)
    * `document_type` (Enum: 'prescription', 'lab_result', 'unknown')
    * `upload_timestamp` (Timestamp)
    * `processing_status` (Enum: 'uploaded', 'ocr_done', 'nlp_done', 'pending_review', 'completed', 'error')
    * `error_message` (Text, nullable)
    * `created_at` (Timestamp)
    * `updated_at` (Timestamp)

* **`extracted_medications`** *(Example - structure depends heavily on NLP output)*
    * `medication_id` (Primary Key, UUID)
    * `document_id` (Foreign Key to `documents`, Indexed)
    * `user_id` (Foreign Key to `users`, Indexed for direct querying)
    * `medication_name` (Text, Indexed)
    * `dosage` (Text)
    * `frequency` (Text)
    * `prescribing_doctor` (Text, nullable)
    * `prescription_date` (Date, nullable, Indexed)
    * `source_text_reference` (JSON/Text - pointer to location in original doc, optional)
    * `is_verified_by_user` (Boolean, default: false)
    * `created_at` (Timestamp)
    * `updated_at` (Timestamp)

* **`extracted_lab_results`** *(Example)*
    * `lab_result_id` (Primary Key, UUID)
    * `document_id` (Foreign Key to `documents`, Indexed)
    * `user_id` (Foreign Key to `users`, Indexed)
    * `test_name` (Text, Indexed)
    * `result_value` (Text - store as text initially due to varied formats, maybe numeric post-validation)
    * `result_unit` (Text, nullable)
    * `reference_range` (Text, nullable)
    * `test_date` (Date, nullable, Indexed)
    * `source_text_reference` (JSON/Text, optional)
    * `is_verified_by_user` (Boolean, default: false)
    * `created_at` (Timestamp)
    * `updated_at` (Timestamp)

* **`notifications`** *(Medical AI Alerts)*
    * `notification_id` (Primary Key, UUID)
    * `user_id` (Foreign Key to `users`, Indexed)
    * `type` (Text - e.g., 'drug_interaction', 'side_effect_warning', 'health_trend')
    * `severity` (Text - 'low', 'medium', 'high')
    * `title` (Text)
    * `message` (Text)
    * `metadata` (JSONB)
    * `is_read` (Boolean, default: false)
    * `is_dismissed` (Boolean, default: false)
    * `expires_at` (Timestamp, nullable)
    * `related_medication_id` (Foreign Key to `medications`, nullable)
    * `related_document_id` (Foreign Key to `documents`, nullable)
    * `related_health_reading_id` (Foreign Key to `health_readings`, nullable)
    * `related_extracted_data_id` (Foreign Key to `extracted_data`, nullable)
    * `created_at` (Timestamp)

* **`medical_situations`** *(Vector Storage for AI)*
    * `situation_id` (Primary Key, UUID)
    * `embedding` (vector(768) - pgvector type for BioBERT embeddings)
    * `medical_context` (JSONB - anonymized medical data)
    * `analysis_result` (JSONB - LLM analysis output)
    * `confidence_score` (Float)
    * `similarity_threshold` (Float, default: 0.85)
    * `usage_count` (Integer, default: 1)
    * `created_at` (Timestamp)
    * `last_used_at` (Timestamp)

* **`ai_analysis_logs`** *(AI Performance Tracking)*
    * `log_id` (Primary Key, UUID)
    * `user_id` (Foreign Key to `users`)
    * `trigger_type` (Text - e.g., 'new_medication', 'symptom_reported')
    * `medical_profile_hash` (Text - for deduplication)
    * `embedding` (vector(768) - query embedding)
    * `similarity_matches` (JSONB - matched situations)
    * `llm_called` (Boolean)
    * `llm_cost` (Float)
    * `processing_time_ms` (Integer)
    * `analysis_result` (JSONB)
    * `related_medication_id` (Foreign Key, nullable)
    * `related_document_id` (Foreign Key, nullable)
    * `related_health_reading_id` (Foreign Key, nullable)
    * `related_extracted_data_id` (Foreign Key, nullable)
    * `created_at` (Timestamp)

* **`audit_log`**
    * `log_id` (Primary Key, Serial/BigSerial)
    * `user_id` (Foreign Key to `users`, nullable if system action)
    * `action_type` (Text - e.g., 'login', 'upload_doc', 'correct_data', 'run_query', 'export_data')
    * `target_resource_type` (Text, nullable - e.g., 'document', 'medication')
    * `target_resource_id` (UUID, nullable)
    * `timestamp` (Timestamp with Time Zone)
    * `details` (JSONB/Text - e.g., IP address, data changes)

*(Indexes are crucial for query performance, especially on `user_id` and date fields)*

## 5. API Design (Key Endpoints - RESTful Style)

*(Base URL: `/api/v1`)*

* **Authentication (Managed by Auth Provider, Backend verifies tokens)**
    * `/auth/token` (or similar, depending on provider) - Handled by frontend interacting with Auth Provider, backend receives token.

* **Documents**
    * `POST /documents/upload_url` - Request a secure signed URL to upload a document directly to object storage from the client.
        * Request: `{ filename: "lab_report.pdf", content_type: "application/pdf" }`
        * Response: `{ upload_url: "...", document_id: "...", storage_path: "..." }`
    * `POST /documents/{document_id}/notify_upload` - Notify backend after successful upload to trigger processing.
    * `GET /documents` - List user's documents with status. (Filters: type, date range)
    * `GET /documents/{document_id}` - Get details of a specific document.
    * `DELETE /documents/{document_id}` - Delete a document and associated extracted data.

* **Extracted Data & Correction**
    * `GET /documents/{document_id}/extracted_data` - Get structured data extracted from a document (for review). Response structure includes flags for `is_verified_by_user`.
    * `PUT /extracted_data/medications/{medication_id}` - Update/correct a specific medication record. Request body contains corrected fields. Sets `is_verified_by_user` to true.
    * `PUT /extracted_data/lab_results/{lab_result_id}` - Update/correct a specific lab result.
    * `POST /documents/{document_id}/verify_all` - Mark all extracted data for a document as reviewed/verified by the user.

* **Data Viewing & Analysis**
    * `GET /medications` - Get list of verified medications. (Filters: current/past, date range).
    * `GET /lab_results` - Get list of verified lab results. (Filters: test name, date range).
    * `GET /lab_results/trends?test_name=...` - Get data points for plotting a specific lab test over time.

* **Natural Language Query**
    * `POST /query` - Submit a natural language query.
        * Request: `{ query_text: "Show my glucose tests from last year" }`
        * Response: `{ query_interpretation: "...", results: [...] }` (Results structure depends on query)

* **Data Export**
    * `POST /export` - Initiate data export job.
    * `GET /export/status/{job_id}` - Check status of export job.
    * `GET /export/download/{job_id}` - Download the exported data (e.g., zip file with originals + CSV/JSON).

*(All endpoints require authentication and authorization checks ensuring users only access their own data)*

## 6. Key User Flows

1.  **User Registration/Login:**
    * User interacts with Frontend UI.
    * Frontend redirects/uses SDK for external Auth Provider (e.g., Firebase Auth).
    * Upon successful auth, Frontend receives an ID token.
    * Frontend sends token to Backend with API requests.
    * Backend verifies token with Auth Provider, identifies/creates user in `users` table, establishes session/context.

2.  **Document Upload & Processing:**
    * User selects file in Mobile App.
    * App requests signed upload URL from Backend (`POST /documents/upload_url`).
    * Backend generates signed URL for secure object storage, creates `documents` record with 'uploaded' status, returns URL + `document_id` to App.
    * App uploads file directly to object storage using the signed URL.
    * Upon successful upload, App notifies Backend (`POST /documents/{document_id}/notify_upload`).
    * Backend triggers async processing task (e.g., via Cloud Tasks/PubSub):
        * Task fetches document from storage.
        * Calls OCR service. Updates status to 'ocr_done'.
        * Calls MedNLP service with OCR text. Updates status to 'nlp_done'.
        * Parses NLP results, stores structured data in `extracted_medications`/`extracted_lab_results` tables (linked to `document_id`, `user_id`, marked as `is_verified_by_user = false`).
        * Updates document status to 'pending_review'. Handles errors and updates status/message accordingly.

3.  **Data Review & Correction:**
    * User navigates to a document needing review in App.
    * App fetches extracted data (`GET /documents/{document_id}/extracted_data`).
    * App displays data, highlighting unverified items, allowing edits.
    * User edits a field (e.g., medication dosage).
    * App sends update request to Backend (`PUT /extracted_data/medications/{medication_id}`).
    * Backend updates the record, sets `is_verified_by_user = true`, logs the change in `audit_log`.
    * User can mark all as verified (`POST /documents/{document_id}/verify_all`), Backend updates relevant records and document status to 'completed'.

4.  **Natural Language Query:**
    * User types query into Mobile App ("What was my cholesterol in March 2024?").
    * App sends query text to Backend (`POST /query`).
    * Backend constructs a prompt for **Gemini 2.5 Flash** (via Vertex AI API). The prompt should include the user's query and potentially context about the available structured data fields (e.g., "User asked: '...'. Available fields are 'test_name', 'result_value', 'test_date', 'medication_name', 'prescription_date'. Extract relevant filters and entities."). **Crucially, do not send raw PHI text snippets in the prompt unless absolutely necessary and the API endpoint guarantees compliance.** Focus on extracting parameters.
    * Vertex AI Gemini API processes the prompt and returns structured output (e.g., `{ "filters": [{"field": "test_name", "operator": "contains", "value": "cholesterol"}, {"field": "test_date", "operator": "between", "value": ["2024-03-01", "2024-03-31"]}] }`).
    * Backend validates the parameters from Gemini.
    * Backend constructs and executes a safe SQL query against the user's *verified* structured data (`extracted_lab_results`, `extracted_medications`) using the parameters.
    * Backend formats the results and sends them back to the Mobile App.
    * App displays the results.

## 7. AI/ML Integration Details

* **OCR/NLP Triggering:** Triggered asynchronously after document upload notification. Use task queues (Cloud Tasks/SQS) for resilience.
* **Input/Output:** Pass document references (storage paths) or potentially byte streams to AI services. Handle responses (usually JSON), parse relevant fields, manage confidence scores if provided.
* **Error Handling:** Implement retry logic for transient API errors. Log persistent errors, update document status, provide user feedback. Handle cases where OCR/NLP fails to extract meaningful data.
* **Gemini Query Integration:**
    * Use **Vertex AI API endpoints** confirmed to support compliance needs (e.g., BAA coverage for HIPAA if applicable).
    * **Prompt Engineering:** Design prompts carefully to guide Gemini to extract query parameters reliably without needing excessive raw PHI context. Focus on schema awareness.
    * **Parameter Validation:** **CRITICAL:** Never directly execute SQL generated by an LLM. Always parse the parameters extracted by the LLM and use them to build queries safely in the backend logic to prevent SQL injection and incorrect data access.
    * **Cost/Latency:** Monitor API usage costs and latency. Consider caching common query interpretations if feasible.

## 8. Security Design

* **Authentication:** Use a managed Auth provider (Firebase Auth, Cognito, Auth0) implementing OAuth 2.0 / OpenID Connect. Store only provider ID in user table. Use short-lived ID tokens/access tokens. Implement refresh token flow securely.
* **Authorization:** All backend API endpoints must verify the user's token and ensure any data access is strictly limited to that `user_id`. Use middleware for this check on relevant routes.
* **Encryption:**
    * **In Transit:** Enforce TLS 1.2+ (HTTPS) for all communication (App <-> Backend, Backend <-> Cloud Services).
    * **At Rest:** Enable encryption features provided by managed database service (e.g., Transparent Data Encryption) and cloud object storage (e.g., Server-Side Encryption). Use provider-managed keys initially for simplicity, consider Customer-Managed Keys (CMEK) if required. Consider application-level encryption for specific sensitive fields if regulatory needs demand it (adds complexity).
* **Compliance (HIPAA/DPDP Act):**
    * Choose cloud services/regions that support relevant compliance standards (e.g., offer BAAs for HIPAA, meet DPDP Act data localization/processing requirements if applicable - **verify this specifically for India**).
    * Configure services according to provider best practices for compliance (e.g., enable detailed logging, restricted network access).
    * Implement data minimization principles (only store necessary data).
    * Ensure robust audit logging (implemented via `audit_log` table).
    * Obtain explicit user consent compliant with DPDP Act requirements for data processing.
    * **Consult with legal/compliance experts specialized in health tech and Indian data privacy laws.**
* **Auditing:** Log key events (logins, data uploads, data modifications, data exports, failed actions) in the `audit_log` table.
* **Input Validation:** Sanitize and validate all input from the client and from AI services (especially LLM query parameters).
* **Dependency Management:** Regularly scan and update dependencies to patch vulnerabilities.

## 9. Infrastructure & Deployment

* **Cloud Environment:** Use separate development/staging/production projects/accounts on GCP/AWS.
* **IaC (Optional but Recommended):** Use Terraform or CloudFormation to define and manage cloud resources consistently.
* **Deployment:**
    * Backend API: Deploy using managed services like Cloud Run/App Engine (GCP) or Elastic Beanstalk/Fargate (AWS). Set up auto-scaling based on load.
    * Frontend App: Build and distribute via standard app stores (Apple App Store, Google Play Store).
* **CI/CD:** Implement a basic CI/CD pipeline (e.g., using GitHub Actions, Cloud Build, Jenkins) for automated testing and deployment.

## 10. Error Handling & Logging

* **Backend:** Implement centralized exception handling. Log errors with context (request ID, user ID if available) using a structured logging library. Use appropriate HTTP status codes for API responses.
* **Frontend:** Handle API errors gracefully, provide user-friendly messages. Log critical frontend errors.
* **Monitoring:** Set up basic monitoring and alerting on cloud resources (CPU, memory, error rates, latency) and application logs.

## 11. Future Considerations

* Scalability of NLP/OCR processing as usage grows.
* Refining NLP models for better accuracy (potential fine-tuning).
* Adding support for more document types.
* Implementing features from the "Out of Scope" list in the PRD.
* More sophisticated data analysis and visualizations.

## 12. Open Questions & Risks

* Achieving acceptable accuracy for OCR/NLP across diverse real-world medical documents.
* Designing a truly intuitive UX for the data review/correction flow.
* Ensuring robust compliance implementation and keeping up with evolving regulations.
* Reliability and cost-effectiveness of the LLM query translation.
* Managing the development workload as a solo developer.