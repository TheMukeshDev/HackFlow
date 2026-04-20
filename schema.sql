-- HackFlow Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    full_name TEXT,
    phone TEXT,
    college TEXT,
    role TEXT DEFAULT 'participant' CHECK (role IN ('participant', 'volunteer', 'admin')),
    provider TEXT DEFAULT 'email',
    provider_id TEXT,
    profile_complete BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Food counters table
CREATE TABLE IF NOT EXISTS public.food_counters (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    is_open BOOLEAN DEFAULT true,
    capacity INTEGER DEFAULT 50,
    average_wait_minutes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Queue entries table
CREATE TABLE IF NOT EXISTS public.queue_entries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    counter_id UUID REFERENCES public.food_counters(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'waiting' CHECK (status IN ('waiting', 'called', 'served', 'cancelled')),
    position INTEGER NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    called_at TIMESTAMP WITH TIME ZONE,
    served_at TIMESTAMP WITH TIME ZONE
);

-- Help requests table
CREATE TABLE IF NOT EXISTS public.help_requests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'resolved')),
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- Notifications table
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crowd zones table
CREATE TABLE IF NOT EXISTS public.crowd_zones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    current_count INTEGER DEFAULT 0,
    max_capacity INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Volunteer assignments table
CREATE TABLE IF NOT EXISTS public.volunteer_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    volunteer_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    zone_id UUID REFERENCES public.crowd_zones(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'offline'))
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.food_counters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.queue_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.help_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crowd_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.volunteer_assignments ENABLE ROW LEVEL SECURITY;

-- RLS Policies (allow all for now - can be tightened later)
CREATE POLICY "Allow all for users" ON public.users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for food_counters" ON public.food_counters FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for queue_entries" ON public.queue_entries FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for help_requests" ON public.help_requests FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for notifications" ON public.notifications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for crowd_zones" ON public.crowd_zones FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all for volunteer_assignments" ON public.volunteer_assignments FOR ALL USING (true) WITH CHECK (true);

-- Insert sample data
INSERT INTO public.food_counters (name, location, description) VALUES
    ('Counter 1', 'Ground Floor - East', 'Main food counter'),
    ('Counter 2', 'Ground Floor - West', 'Secondary food counter'),
    ('Counter 3', 'First Floor', 'Vegan options')
ON CONFLICT DO NOTHING;

INSERT INTO public.crowd_zones (name, max_capacity) VALUES
    ('Main Hall', 100),
    ('Food Court', 50),
    ('Workshop Area', 30)
ON CONFLICT DO NOTHING;