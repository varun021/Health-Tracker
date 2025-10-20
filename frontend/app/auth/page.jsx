'use client';

import { useState } from 'react';
import Link from 'next/link';
import { LoginForm } from '@/components/login-form';
import { SignupForm } from '@/components/signup-form';

export default function AuthPage() {
  const [tab, setTab] = useState('login');

  const tabClass = (active) =>
    `px-4 py-2 rounded-md font-medium transition ${
      active ? 'bg-primary text-white' : 'bg-muted hover:bg-muted/80'
    }`;

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-4xl">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex gap-2">
            <button onClick={() => setTab('login')} className={tabClass(tab === 'login')}>
              Login
            </button>
            <button onClick={() => setTab('signup')} className={tabClass(tab === 'signup')}>
              Sign up
            </button>
          </div>
          <div className="text-sm">
            <Link href="/login" className="underline mr-3">
              Open login page
            </Link>
            <Link href="/signup" className="underline">
              Open signup page
            </Link>
          </div>
        </div>

        <section>
          {tab === 'login' ? <LoginForm /> : <SignupForm />}
        </section>
      </div>
    </main>
  );
}