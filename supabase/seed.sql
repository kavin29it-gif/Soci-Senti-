-- Supabase Seed Data for Development and Testing

-- Starter Analyst & Reviewer profiles
INSERT INTO public.profiles (id, email, full_name, role)
VALUES
    ('a0000000-0000-0000-0000-000000000001', 'analyst@socisenti.local', 'Sarah Chen (Senior Analyst)', 'analyst'),
    ('a0000000-0000-0000-0000-000000000002', 'reviewer@socisenti.local', 'Marcus Vance (Compliance Lead)', 'reviewer'),
    ('a0000000-0000-0000-0000-000000000003', 'admin@socisenti.local', 'Dev Administrator', 'admin')
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = EXCLUDED.full_name,
    role = EXCLUDED.role;

-- Initial Demo Case
INSERT INTO public.cases (
    id,
    title,
    description,
    status,
    priority,
    created_by,
    reviewer_approved
)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'Investigation: Coordinated Disinformation Campaign #849',
    'Monitoring anomalous burst of coordinated synthetic narratives across Telegram and Reddit with elevated toxicity and market manipulation keywords.',
    'investigating',
    'high',
    'a0000000-0000-0000-0000-000000000001',
    false
)
ON CONFLICT (id) DO NOTHING;

-- Seed Case Note
INSERT INTO public.case_notes (
    id,
    case_id,
    author_id,
    note
)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'c0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'Initial triage: Cluster of 14 accounts flagged by NetworkX Louvain community detection posting near-identical text within 45 seconds.'
)
ON CONFLICT (id) DO NOTHING;
