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
import { useAuthStore } from "@/stores/auth-store";

const PASSWORD_MIN_LENGTH = 12;

export function RegisterForm() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      await authApi.register({
        email,
        password,
        full_name: fullName.trim() ? fullName.trim() : null,
      });
      return authApi.login({ email, password });
    },
    onSuccess: (pair) => {
      useAuthStore.getState().setTokens(pair);
      toast.success("Account created");
      router.replace("/dashboard");
    },
  });

  const error = mutation.error;
  const errorMessage =
    validationError ??
    (error instanceof ApiError
      ? error.status === 429
        ? "Too many attempts. Please wait a few minutes and try again."
        : error.detail
      : error
        ? "Unexpected error. Please try again."
        : null);

  return (
    <Card>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          setValidationError(null);
          if (password.length < PASSWORD_MIN_LENGTH) {
            setValidationError(
              `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`,
            );
            return;
          }
          if (password !== confirmPassword) {
            setValidationError("Passwords do not match.");
            return;
          }
          mutation.mutate();
        }}
      >
        <CardHeader>
          <CardTitle>Create account</CardTitle>
          <CardDescription>
            Sign up for access to the IAM console.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {errorMessage ? (
            <Alert variant="destructive">
              <AlertTitle>Registration failed</AlertTitle>
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          ) : null}
          <div className="space-y-2">
            <Label htmlFor="full-name">Full name (optional)</Label>
            <Input
              id="full-name"
              autoComplete="name"
              placeholder="Jane Doe"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="register-email">Email</Label>
            <Input
              id="register-email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="register-password">Password</Label>
            <Input
              id="register-password"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={PASSWORD_MIN_LENGTH}
              required
            />
            <p className="text-xs text-muted-foreground">
              At least {PASSWORD_MIN_LENGTH} characters.
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm-password">Confirm password</Label>
            <Input
              id="confirm-password"
              type="password"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              minLength={PASSWORD_MIN_LENGTH}
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
            Create account
          </Button>
          <p className="text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-primary hover:underline"
            >
              Sign in
            </Link>
          </p>
        </CardFooter>
      </form>
    </Card>
  );
}
