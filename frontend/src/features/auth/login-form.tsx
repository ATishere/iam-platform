"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { authApi } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { usersApi } from "@/lib/api/users";
import { useAuthStore } from "@/stores/auth-store";

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => authApi.login({ email, password }),
    onSuccess: async (pair) => {
      useAuthStore.getState().setTokens(pair);
      try {
        const user = await usersApi.me();
        useAuthStore.getState().setUser(user);
      } catch {
        useAuthStore.getState().setUser(null);
      }
      toast.success("Signed in successfully");
      router.replace("/dashboard");
    },
  });

  const error = mutation.error;
  const errorMessage =
    error instanceof ApiError
      ? error.status === 429
        ? "Too many login attempts. Please wait a minute and try again."
        : error.detail
      : error
        ? "Unexpected error. Please try again."
        : null;

  return (
    <Card>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate();
        }}
      >
        <CardHeader>
          <CardTitle>Sign in</CardTitle>
          <CardDescription>
            Use your account credentials to access the console.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {errorMessage ? (
            <Alert variant="destructive">
              <AlertTitle>Sign in failed</AlertTitle>
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4">
          <Button
            type="submit"
            className="w-full"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? <Spinner className="text-primary-foreground" /> : null}
            Sign in
          </Button>
          <p className="text-sm text-muted-foreground">
            No account yet?{" "}
            <Link
              href="/register"
              className="font-medium text-primary hover:underline"
            >
              Create one
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
