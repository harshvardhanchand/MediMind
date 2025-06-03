# Tech Stack PRD: AI-Powered Patient Medical Data Hub (Updated)

## 1. Introduction

This document outlines the technical requirements for the initial phase of an AI-native mobile application designed to empower patients to securely store, manage, analyze, and query their personal medical data, focusing initially on prescriptions and test results. The application's primary goal is patient empowerment through data access and basic trend identification, **explicitly avoiding the provision of medical advice or clinical interpretation.**

## 2. Product Scope (Initial Phase)

The initial phase focuses on core functionalities enabling users to consolidate and understand their own documented medical history:

* **Secure Document Upload & Storage:** Allow users to upload digital copies (e.g., PDFs, common image formats) of prescriptions and lab/test results via the mobile app. Store these raw documents securely in a compliant storage solution.
* **AI-Powered Data Parsing & Extraction:** Utilize appropriate AI/ML techniques (including Optical Character Recognition and Natural Language Processing specifically trained or adapted for medical documents) to extract key structured data points (e.g., medication name, dosage, frequency, prescribing doctor, date; lab test name, result value, reference range, units, date of test).
* **Structured Data Storage:** Store the extracted, structured medical data securely in a database associated with the user's profile, linking it to the source document.
* **User Data Review & Correction:** Provide a clear and intuitive interface for users to review the extracted data *before* it is finalized and make necessary corrections. Maintain an audit trail of user corrections.
* **Basic Data Visualization & Listing:** Offer simple visualizations and lists based on the structured data, such as:
    * Plotting specific, user-selected lab test results over time.
    * Listing current or past medications based on user-defined date ranges.
    * Displaying lab results alongside their provided reference ranges (without flagging or interpreting high/low values).
* **AI-Powered Natural Language Querying:** Enable users to query their *structured* data using natural language (e.g., "Show my glucose tests from 2024," "What medications did Dr. Anya Sharma prescribe?"). This functionality will leverage an LLM like **Gemini 2.5 Flash** (accessed via compliant API endpoints) to interpret the natural language query and translate it into database query parameters.
* **Secure User Authentication & Authorization:** Implement robust user registration, login, and session management to ensure only the authenticated user can access their data.
* **User-Controlled Data Export:** Provide a mechanism for users to export their data, including both the original uploaded documents and the extracted structured data, in common, usable formats.
* **Proactive Medical AI Notifications:** Implement an intelligent notification system that proactively analyzes medical data for potential drug interactions, side effects, health trends, and provides personalized recommendations before they become serious problems. Uses BioBERT embeddings and Gemini LLM with vector similarity caching for cost-effective analysis.
* **Mobile User Interface:** A mobile-first, intuitive interface for all functionalities: document upload, data review/correction, viewing visualizations/lists, performing queries, managing notifications, and managing account settings.
* **Clear Disclaimers:** Prominently display clear, understandable disclaimers throughout the application reinforcing that it does **not** provide medical advice, diagnosis, or treatment recommendations, and that users should always consult qualified healthcare professionals for medical concerns.

### Out of Scope (Initial Phase):

* Providing any form of medical advice, interpretation, diagnosis, or treatment suggestions.
* Real-time symptom tracking.
* Integration with wearables or other personal health devices.
* Direct integration with EHR systems, hospital/lab portals, or pharmacies for automatic data import.
* Data sharing features (with providers or others).
* Complex clinical decision support features.

## 3. Key Technical Components & Requirements

### Frontend (Mobile Application):

* Built using a **cross-platform mobile development framework** to target both iOS and Android efficiently.
* Intuitive UX/UI, potentially accelerated by a **UI component library**.
* Secure handling of user credentials and data display.
* Access to device camera/storage for uploads.
* Secure communication (HTTPS) with the backend API.
* Robust error handling and user-friendly feedback mechanisms.
* Clear onboarding flow explaining features, security measures, data usage policies, and application limitations (especially the "no medical advice" policy).

### Backend (API & Business Logic):

* Developed using a **backend programming language and framework** suitable for secure API development, complex business logic, and integration with AI/ML services.
* Handles secure user authentication/authorization (e.g., using standard protocols like OAuth 2.0).
* Manages document uploads to secure object storage.
* Orchestrates the data processing pipeline (calling OCR/NLP services/models).
* Handles storage and retrieval of structured data from the database.
* Implements the logic for basic analysis/visualization endpoints.
* Processes natural language queries (potentially via **Gemini 2.5 Flash**) and translates them into database queries.
* Serves data securely to the frontend.
* Designed with compliance requirements (e.g., HIPAA, GDPR, **DPDP Act 2023**) in mind.

### Database:

* A **secure, scalable, managed relational database service**.
* Must offer features supporting compliance (e.g., encryption at rest and in transit, audit logging, backup/recovery, BAA availability if applicable).
* Capable of handling structured medical data and supporting the queries needed for analysis and user requests.
* Separate **secure, compliant cloud object storage service** for raw document storage (linked from the relational database).

### AI/ML Component:

* **OCR:** Leverages suitable **AI/ML models or cloud-based services** for accurate text extraction from diverse document images/PDFs.
* **NLP/Data Extraction:** Employs appropriate **AI/ML models or specialized medical NLP cloud services** (potentially pre-trained on medical text, e.g., exploring options like Google Cloud Healthcare Natural Language API, AWS Comprehend Medical, or developing custom models) to identify and extract specific structured data points from the OCR output.
* **Natural Language Querying:** Utilizes an LLM such as **Gemini 2.5 Flash**, accessed via **secure and compliant API endpoints** (e.g., Google Cloud Vertex AI Gemini API with appropriate configurations and agreements), to parse user's natural language questions and translate them into structured database query parameters for the backend to execute. Requires careful prompt engineering and validation.
* **Analysis Logic:** Basic trend identification (e.g., plotting values over time) and data listing implemented primarily in the **backend business logic**, operating on the structured data retrieved from the database.

### Data Input/Processing Pipeline:

* Handles various input formats (PDF, JPG, PNG, etc.).
* Orchestrates calls to OCR and NLP components.
* Includes a **critical user review and correction step** within the mobile UI before data is finalized in the database. This interface must be intuitive and allow for easy modification of potentially complex extracted data.
* Implements robust error handling for parsing failures and provides feedback to the user.
* Includes an audit trail for data origin and user corrections.

### Security and Compliance:

* End-to-end encryption (data in transit via HTTPS, data at rest in database and object storage).
* Strong authentication and authorization mechanisms.
* Role-based access control principles (even if only one user role initially).
* Comprehensive logging and auditing capabilities.
* Adherence to relevant data privacy and health data regulations (e.g., HIPAA, GDPR, **DPDP Act 2023**). Requires careful implementation and potentially legal/compliance consultation.
* Regular security patching and vulnerability management for all components and dependencies.
* Implementation of prominent in-app disclaimers regarding the tool's limitations (no medical advice).

### Infrastructure:

* Hosted on a **major cloud computing platform** (e.g., AWS, GCP, Azure) offering necessary managed services and compliance support (e.g., BAAs where applicable, features supporting DPDP Act requirements).
* Prioritize **managed services** (database, object storage, potentially compute/deployment platforms, AI APIs) to reduce operational overhead.
* Utilize cloud provider security features (network isolation, firewalls, identity management).
* Employ a **deployment mechanism suitable for scaling and management** (e.g., managed app platforms, serverless functions, or container orchestration if complexity warrants it).

## 4. Technical Challenges and Considerations

* **Data Extraction Accuracy:** Achieving high accuracy across diverse medical document formats remains a primary challenge. The user correction workflow is vital.
* **Compliance Overhead:** Meeting and maintaining compliance with health data regulations (HIPAA, DPDP Act, etc.) is complex, costly, and requires ongoing effort and expertise.
* **Security Implementation:** Requires meticulous design and implementation across the entire stack.
* **LLM Integration for Queries:** Ensuring the compliant use of **Gemini 2.5 Flash** (via appropriate secure/compliant APIs), managing API costs, latency, and ensuring accurate translation of intent to queries.
* **Usability:** Designing an intuitive interface for potentially complex data review and correction is critical for user adoption and data quality.
* **Cost Management:** Cloud services (especially AI APIs, managed databases, storage) incur ongoing costs that need monitoring.
* **Solo Developer Workload:** The breadth of work (frontend, backend, AI, security, compliance, ops) is substantial for one person.

## 5. Non-Functional Requirements

* **Performance:** Responsive UI, reasonably fast document processing (acknowledging AI task latency), and quick query results.
* **Reliability:** High availability of the service with minimal downtime.
* **Security:** Meet or exceed industry standards and regulatory requirements for sensitive health data.
* **Scalability:** Architecture should support growth in users and data volume.
* **Maintainability:** Well-structured, documented code.
* **Usability:** Intuitive and accessible for users with varying technical literacy. Requires clear onboarding and help resources.
* **Data Integrity:** Ensure accuracy through robust extraction, validation, and user correction processes.

## 6. Phased Development Approach (Suggested)

### Phase 1 (Core Secure Foundation):

* User Authentication & Profile Management.
* Secure Backend API setup.
* Secure Database & Object Storage setup (compliant services).
* Basic Document Upload & Secure Storage.
* Simple Document Listing/Retrieval.
* **Focus:** Establish the secure, compliant storage and user management core.

### Phase 2 (Parsing & Review):

* Integrate OCR & NLP services/models.
* Implement the backend data extraction pipeline.
* Develop the crucial User Review & Correction UI/flow.
* Store structured data in the database.
* Implement basic structured data display (e.g., simple lists).
* Implement Data Export feature.
* **Focus:** Enable accurate data extraction with user validation.

### Phase 3 (Analysis & Querying):

* Implement basic visualization features (e.g., plotting specific lab values).
* Integrate **Gemini 2.5 Flash** (via compliant API) for natural language query interpretation.
* Implement backend logic to execute database queries based on LLM output.
* Refine UI for analysis and querying.
* **Focus:** Add value through basic analysis and natural language interaction.

### Phase 4 (Medical AI Notifications):

* Implement proactive medical AI notification system with BioBERT embeddings and Gemini Pro analysis.
* Add vector similarity search using pgvector for cost-effective medical pattern recognition.
* Create comprehensive notification management with severity levels and entity relationships.
* Integrate automatic triggers for medication, symptom, lab result, and document events.
* **Focus:** Proactive health monitoring and intelligent medical alerts.

### Phase 5+ (Refinements & Future Scope):

* Improve parsing accuracy based on feedback.
* Enhance analysis/visualization features.
* Explore features from the "Out of Scope" list (symptom tracking, integrations) based on user needs and feasibility.

## 7. Conclusion

This project aims to provide significant value to patients by helping them manage their own health data. While the technology choices remain flexible (except for the specified use of **Gemini 2.5 Flash** for querying), the core requirements emphasize security, compliance (including HIPAA and DPDP Act), data accuracy via user validation, and a clear boundary against providing medical advice. The phased approach is crucial for managing the complexity, particularly for a solo developer. Success hinges on meticulous implementation of security/compliance measures and creating a highly usable data review process.