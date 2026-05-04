<route lang="yaml">
meta:
  layout: auth
</route>

<template>
  <Card class="max-w-2xl w-full">
    <CardHeader>
      <CardTitle class="text-lg">Terms of Service</CardTitle>
      <CardDescription>Last updated: May 2026</CardDescription>
    </CardHeader>
    <CardContent class="prose prose-sm max-w-none text-sm text-muted-foreground space-y-4">
      <p>By creating an account and using our service you agree to the following terms.</p>

      <h3 class="font-semibold text-foreground">Acceptable Use</h3>
      <p>
        You agree not to use the service for illegal purposes, to infringe intellectual property
        rights, or to distribute malicious software.
      </p>

      <h3 class="font-semibold text-foreground">Account Responsibility</h3>
      <p>
        You are responsible for maintaining the confidentiality of your account credentials and for
        all activity that occurs under your account.
      </p>

      <h3 class="font-semibold text-foreground">Service Availability</h3>
      <p>
        We strive to maintain high availability but do not guarantee uninterrupted access to the
        service.
      </p>

      <h3 class="font-semibold text-foreground">Termination</h3>
      <p>
        We reserve the right to suspend or terminate accounts that violate these terms. You may
        delete your account at any time from your account settings.
      </p>

      <h3 class="font-semibold text-foreground">Changes to Terms</h3>
      <p>
        We may update these terms from time to time. Continued use of the service after changes
        constitutes acceptance of the revised terms.
      </p>

      <h3 class="font-semibold text-foreground">Contact</h3>
      <p>For questions about these terms please contact us at legal@example.com.</p>
    </CardContent>
  </Card>
</template>

<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
</script>
