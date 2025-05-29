# Ticket System ER Diagram

```mermaid
erDiagram
    Company ||--o{ User : "has many"
    User ||--o{ Ticket : "creates"
    User ||--o{ TicketComment : "creates"
    User ||--o{ TicketAttachment : "uploads"
    User |o--o{ Ticket : "assigned to"
    User |o--o{ Ticket : "tagged in"
    Company ||--o{ ServiceFamily : "has"
    Company ||--o{ Ticket : "owns"
    
    ServiceFamily ||--o{ ServiceType : "has"
    ServiceType ||--o{ ServiceCategory : "has"
    ServiceCategory |o--o{ Ticket : "categorizes"
    
    Ticket ||--o{ TicketComment : "has"
    Ticket ||--o{ TicketAttachment : "has"
    
    User ||--|| Profile : "has one"
    
    Company {
        int id PK
        string name
        string slug UK
        string address
        string phone
        boolean is_active
        datetime created_at
    }
    
    User {
        int id PK
        int company_id FK
        string username
        string password
        string email
        boolean is_active
        boolean is_staff
        boolean is_superuser
    }
    
    Profile {
        int id PK
        int user_id FK "OneToOne"
        string job_title
        string location
        string phone
        string profile_picture
        string timezone
        string language
        boolean email_notifications
        datetime created_at
        datetime updated_at
    }
    
    ServiceFamily {
        int id PK
        int company_id FK
        string name
        string description
        datetime created_at
        datetime updated_at
    }
    
    ServiceType {
        int id PK
        int family_id FK
        string name
        string description
        datetime created_at
        datetime updated_at
    }
    
    ServiceCategory {
        int id PK
        int service_type_id FK
        string name
        string description
        datetime created_at
        datetime updated_at
    }
    
    Ticket {
        int id PK
        string title
        text description
        string status
        string impact
        string priority
        int company_id FK
        int category_id FK
        int created_by_id FK
        int assigned_to_id FK
        datetime created_at
    }
    
    TicketAttachment {
        int id PK
        int ticket_id FK
        string file
        string filename
        string file_type
        int size
        int uploaded_by_id FK
        datetime uploaded_at
    }
    
    TicketComment {
        int id PK
        int ticket_id FK
        text text
        int created_by_id FK
        datetime created_at
        datetime updated_at
    }