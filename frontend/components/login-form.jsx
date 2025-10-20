"use client";
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { userApi } from "@/lib/api-services"
import useAuthStore from "@/stores/useAuthStore"
import { toast } from "sonner"
import Image from "next/image"

export function LoginForm({ className, ...props }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const setUser = useAuthStore((s) => s.setUser);
  const router = useRouter();

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    
    if (!username.trim() || !password) {
      toast.error("Please enter both username and password");
      return;
    }

    setLoading(true);
    
    try {
      await userApi.login({ username, password });
      const profile = await userApi.getProfile();
      setUser(profile);
      toast.success("Login successful! Redirecting...");
      router.push("/dashboard");
    } catch (err) {
      const errorMsg = err?.response?.data?.detail ?? err?.message ?? "Login failed";
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [username, password, setUser, router]);

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden p-0">
        <CardContent className="grid p-0 md:grid-cols-2">
          <form onSubmit={handleSubmit} className="p-6 md:p-8">
            <FieldGroup>
              <div className="flex flex-col items-center gap-2 text-center">
                <h1 className="text-2xl font-bold">Welcome back</h1>
                <p className="text-muted-foreground text-balance">
                  Login to your Acme Inc account
                </p>
              </div>
              
              <Field>
                <FieldLabel htmlFor="username">Username</FieldLabel>
                <Input 
                  id="username" 
                  value={username} 
                  onChange={(e) => setUsername(e.target.value)} 
                  placeholder="username" 
                  autoComplete="username"
                  disabled={loading}
                  required 
                />
              </Field>
              
              <Field>
                <div className="flex items-center">
                  <FieldLabel htmlFor="password">Password</FieldLabel>
                  <a 
                    href="/forgot-password" 
                    className="ml-auto text-sm underline-offset-2 hover:underline"
                    tabIndex={-1}
                  >
                    Forgot your password?
                  </a>
                </div>
                <Input 
                  id="password" 
                  type="password" 
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)} 
                  autoComplete="current-password"
                  disabled={loading}
                  required 
                />
              </Field>
              
              <Field>
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Logging in..." : "Login"}
                </Button>
              </Field>
              
              <FieldDescription className="text-center">
                Don&apos;t have an account?{" "}
                <a href="/signup" className="underline underline-offset-2 hover:text-primary">
                  Sign up
                </a>
              </FieldDescription>
            </FieldGroup>
          </form>
          
          <div className="bg-muted relative hidden md:block">
            <Image
              src="/image-3.jpg"
              alt="Login illustration"
              fill
              className="object-cover dark:brightness-[0.2] dark:grayscale"
              priority
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}