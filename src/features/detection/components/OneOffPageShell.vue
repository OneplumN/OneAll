<template>
  <RepositoryPageShell
    :root-title="rootTitle"
    :section-title="sectionTitle"
    :breadcrumb="breadcrumb"
    :body-padding="bodyPadding"
    :panel-bordered="panelBordered"
  >
    <template #actions>
      <slot name="actions" />
    </template>

    <slot />

    <template
      v-if="$slots.footer"
      #footer
    >
      <slot name="footer" />
    </template>
  </RepositoryPageShell>
</template>

<script setup lang="ts">
import RepositoryPageShell from '@/shared/components/layout/RepositoryPageShell';

withDefaults(
  defineProps<{
    rootTitle?: string;
    sectionTitle: string;
    breadcrumb?: string;
    bodyPadding?: string;
    panelBordered?: boolean;
  }>(),
  {
    rootTitle: '一次性检验',
    breadcrumb: '',
    bodyPadding: '0',
    panelBordered: true
  }
);
</script>
