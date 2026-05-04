<route lang="yaml">
meta:
  layout: auth
</route>

<template>
  <Card class="max-w-2xl w-full">
    <CardHeader>
      <CardTitle class="text-lg">Privacy Policy</CardTitle>
      <CardDescription>Last updated: May 2026</CardDescription>
    </CardHeader>
    <CardContent class="prose prose-sm max-w-none text-sm text-muted-foreground space-y-4">
      <p>
        This Privacy Policy describes how we collect, use, and protect your personal data when you
        use our service.
      </p>

      <h3 class="font-semibold text-foreground">Data We Collect</h3>
      <p>We collect your name, email address, and account activity data to provide our service.</p>

      <h3 class="font-semibold text-foreground">How We Use Your Data</h3>
      <p>
        We use your data to operate the service, send transactional emails, and comply with legal
        obligations.
      </p>

      <h3 class="font-semibold text-foreground">Third-Party Services</h3>
      <p>
        We use Stripe for payment processing and an SMTP provider for transactional emails. These
        services may receive your email address and billing information as required to deliver our
        service.
      </p>

      <h3 class="font-semibold text-foreground">Your Rights</h3>
      <p>
        Under GDPR you have the right to access, rectify, export, and erase your personal data. You
        can exercise these rights from your account settings under
        <RouterLink to="/settings/privacy" class="underline">Privacy &amp; Data</RouterLink>.
      </p>

      <h3 class="font-semibold text-foreground">Data Retention</h3>
      <p>
        We retain your account data for as long as your account is active. Deleted accounts are
        permanently purged after a 30-day grace period.
      </p>

      <h3 class="font-semibold text-foreground">Contact</h3>
      <p>For privacy-related inquiries please contact us at privacy@example.com.</p>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
</script>
