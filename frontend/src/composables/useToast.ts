import { useToast as useShadcnToast } from '@/components/ui/toast/use-toast'

export function useToast() {
  const { toast } = useShadcnToast()
  return { toast }
}
