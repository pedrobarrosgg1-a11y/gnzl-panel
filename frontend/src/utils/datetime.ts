/**
 * Datas da API chegam em UTC (ISO-8601 com "Z"). A interface mostra no
 * horário de Brasília, que é o fuso das campanhas deste projeto.
 */
const TIME_ZONE = "America/Sao_Paulo";

const dateFormatter = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeZone: TIME_ZONE,
});

const dateTimeFormatter = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: TIME_ZONE,
});

function parse(value: string): Date | null {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function formatDate(value: string): string {
  const date = parse(value);
  return date ? dateFormatter.format(date) : "—";
}

export function formatDateTime(value: string): string {
  const date = parse(value);
  return date ? dateTimeFormatter.format(date) : "—";
}
