# System Diagrams

## ER Diagram
```mermaid
erDiagram
    User {
        string username
        string email
        string first_name
        string last_name
        boolean is_staff
        boolean is_active
        boolean is_company_agent
        datetime date_joined
    }
    
    Company {
        string name
        string slug
        text address
        string phone
        boolean is_active
        datetime created_at
    }
    
    Profile {
        string phone_number
        string profile_picture
        boolean mfa_enabled
        string mfa_secret
        boolean mfa_verified
        boolean first_login_completed
        string job_title
        string location
        string timezone
        string language
        boolean email_notifications
        string password_reset_token
        datetime password_reset_token_created
        datetime created_at
        datetime updated_at
    }
    
    ServiceFamily {
        string name
        text description
        datetime created_at
        datetime updated_at
    }
    
    ServiceType {
        string name
        text description
        datetime created_at
        datetime updated_at
    }
    
    ServiceCategory {
        string name
        text description
        datetime created_at
        datetime updated_at
    }
    
    Ticket {
        string title
        text description
        string status
        string impact
        string priority
        datetime created_at
        datetime updated_at
    }
    
    TicketComment {
        text text
        datetime created_at
        datetime updated_at
    }
    
    TicketAttachment {
        file file
        string filename
        string file_type
        integer size
        datetime uploaded_at
    }

    User ||--o{ Profile : has
    User }o--|| Company : belongs_to
    Company ||--o{ ServiceFamily : has
    ServiceFamily ||--o{ ServiceType : has
    ServiceType ||--o{ ServiceCategory : has
    ServiceCategory ||--o{ Ticket : has
    Company ||--o{ Ticket : has
    User ||--o{ Ticket : created_by
    User ||--o{ Ticket : assigned_to
    User }o--o{ Ticket : contacts
    Ticket ||--o{ TicketComment : has
    Ticket ||--o{ TicketAttachment : has
    User ||--o{ TicketComment : created_by
    User ||--o{ TicketAttachment : uploaded_by
```

## Architecture Diagram
```mermaid
graph TD
    A[Client Browser] --> B[Django Web Server]
    B --> C[URL Dispatcher]
    C --> D[Views Layer]
    D --> E[Authentication/Authorization]
    D --> F[Business Logic]
    F --> G[Models Layer]
    G --> H[(PostgreSQL Database)]
    D --> I[Template Layer]
    I --> J[Static Files]
    I --> K[Media Files]
    L[Email Service] --> D
```