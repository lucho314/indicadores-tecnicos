import { LoginForm } from "../components/LoginForm"

export function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-foreground">Trading Strategy</h1>
          <p className="mt-2 text-muted-foreground">Accede a tu panel de administración</p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}
