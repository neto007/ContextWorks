# 🎨 Guia de Estilos e UI

O ContextWorks Frontend utiliza uma abordagem moderna de estilização baseada no **Tailwind CSS v4** e componentes **Radix UI** (através da biblioteca shadcn/ui).

## Filosofia de Design

Buscamos uma interface:
- **Limpa e Minimalista**: Foco no conteúdo (código e logs).
- **Consistente**: Uso estrito de tokens de design.
- **Acessível**: Todos os componentes devem ser navegáveis via teclado e ter suporte a leitores de tela.

## Tailwind CSS v4

Utilizamos a versão mais recente do Tailwind. A configuração principal está em `src/index.css` (onde as variáveis CSS de tema são definidas).

### Cores Semânticas
Não use cores hardcoded (ex: `bg-blue-500`). Use os tokens semânticos:
- `bg-primary` / `text-primary-foreground`: Ação principal.
- `bg-destructive` / `text-destructive-foreground`: Ações de erro/perigo.
- `bg-muted`: Elementos secundários ou desabilitados.

### Espaçamento e Layout
- Use `flex` e `grid` para layouts.
- Prefira `gap-x` em vez de margens para espaçamento entre elementos filhos.
- Use `container` para centralizar conteúdo principal.

## Biblioteca de Componentes (`src/components/ui`)

Os componentes base (Button, Input, Card, Dialog) residem em `src/components/ui`. Eles são "headless" do Radix UI estilizados com Tailwind.

### Exemplo de Uso

```tsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export function FeatureCard() {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <CardTitle>Nova Feature</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground mb-4">Descrição da feature.</p>
        <Button variant="default">Ativar</Button>
      </CardContent>
    </Card>
  )
}
```

## Ícones

Utilizamos **Lucide React**. Ícones devem ser importados individualmente para tree-shaking eficiente.

```tsx
import { Activity, Settings } from "lucide-react";
```

## Animações

Utilizamos `tailwindcss-animate` para micro-interações rápidas:
- `animate-in` / `animate-out` para modais e dropdowns.
- `fade-in`, `slide-in-from-bottom` são classes utilitárias disponíveis.
