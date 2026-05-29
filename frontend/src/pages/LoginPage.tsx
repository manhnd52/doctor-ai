import React, { useState, useEffect } from "react"
import { useNavigate, useLocation } from "react-router-dom"
import { useUserStore } from "../store/userStore"
import { authService } from "../services/authService"
import { User, Lock, Eye, EyeOff, LogIn, UserPlus, Loader2, AlertCircle } from "lucide-react"
import chatbotLogo from "../assets/chatbot-ai.jpeg"

import LoginHeader from "../components/LoginHeader"
import LoginTabs from "../components/LoginTabs"
import LoginInput from "../components/LoginInput"

export default function Login() {
    const navigate = useNavigate()
    const location = useLocation()
    const { login, register, token, error, loading, clearError } = useUserStore()

    const [isLoginTab, setIsLoginTab] = useState(true)
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [confirmPassword, setConfirmPassword] = useState("")
    const [showPassword, setShowPassword] = useState(false)
    const [validationError, setValidationError] = useState<string | null>(null)

    // Redirect if already logged in
    useEffect(() => {
        if (token) {
            const from = (location.state as any)?.from?.pathname || "/"
            navigate(from, { replace: true })
        }
    }, [token, navigate, location])

    // Clear errors when switching tabs
    useEffect(() => {
        clearError()
        setValidationError(null)
    }, [isLoginTab, clearError])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setValidationError(null)
        clearError()

        const valError = isLoginTab
            ? authService.validateLogin(username, password)
            : authService.validateRegister(username, password, confirmPassword)

        if (valError) {
            setValidationError(valError)
            return
        }

        if (!isLoginTab) {
            const success = await register(username, password)
            if (success) {
                navigate("/")
            }
        } else {
            const success = await login(username, password)
            if (success) {
                navigate("/")
            }
        }
    }

    return (
        <div className="relative flex min-h-screen w-screen items-center justify-center bg-secondary px-4 font-sans text-primary select-none">
            {/* Subtle Background Glows matching Light/Accent Theme */}
            <div className="absolute top-[-10%] left-[-10%] h-[400px] w-[400px] rounded-full bg-accent/5 blur-[100px] pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] h-[400px] w-[400px] rounded-full bg-accent/5 blur-[100px] pointer-events-none" />

            {/* Main Container */}
            <div className="z-10 w-full max-w-[420px] rounded-2xl border border-theme bg-panel p-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] animate-fadeIn">
                {/* Logo and Header */}
                <LoginHeader logoSrc={chatbotLogo} />

                {/* Tab Selector */}
                <LoginTabs isLoginTab={isLoginTab} onTabChange={setIsLoginTab} />

                {/* Form */}
                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    {/* Error Message */}
                    {(error || validationError) && (
                        <div className="flex items-start gap-2.5 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs text-red-600 transition-all">
                            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                            <span>{validationError || error}</span>
                        </div>
                    )}

                    {/* Username Input */}
                    <LoginInput
                        label="Username"
                        icon={<User className="h-4 w-4" />}
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter username..."
                        disabled={loading}
                    />

                    {/* Password Input */}
                    <LoginInput
                        label="Password"
                        icon={<Lock className="h-4 w-4" />}
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter password..."
                        disabled={loading}
                        rightElement={
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                disabled={loading}
                                className="text-secondary/60 hover:text-primary transition disabled:opacity-50 cursor-pointer"
                            >
                                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                        }
                    />

                    {/* Confirm Password (for Register) */}
                    {!isLoginTab && (
                        <div className="animate-fadeIn">
                            <LoginInput
                                label="Confirm Password"
                                icon={<Lock className="h-4 w-4" />}
                                type={showPassword ? "text" : "password"}
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Re-enter password..."
                                disabled={loading}
                            />
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        type="submit"
                        disabled={loading}
                        className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent py-3 text-sm font-semibold text-white shadow-sm hover:shadow-md hover:brightness-105 active:scale-98 transition-all disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
                    >
                        {loading ? (
                            <Loader2 className="h-4.5 w-4.5 animate-spin" />
                        ) : isLoginTab ? (
                            <>
                                <LogIn className="h-4.5 w-4.5" />
                                <span>Sign In</span>
                            </>
                        ) : (
                            <>
                                <UserPlus className="h-4.5 w-4.5" />
                                <span>Create Account</span>
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    )
}
