export interface TimezoneOption {
  value: string;
  label: string;
  offset: string;
}

export interface TimezoneGroup {
  region: string;
  timezones: TimezoneOption[];
}

export const TIMEZONE_GROUPS: TimezoneGroup[] = [
  {
    region: "Americas",
    timezones: [
      { value: "America/New_York", label: "New York", offset: "UTC-5/-4" },
      { value: "America/Chicago", label: "Chicago", offset: "UTC-6/-5" },
      { value: "America/Denver", label: "Denver", offset: "UTC-7/-6" },
      { value: "America/Los_Angeles", label: "Los Angeles", offset: "UTC-8/-7" },
      { value: "America/Anchorage", label: "Anchorage", offset: "UTC-9/-8" },
      { value: "Pacific/Honolulu", label: "Honolulu", offset: "UTC-10" },
      { value: "America/Toronto", label: "Toronto", offset: "UTC-5/-4" },
      { value: "America/Vancouver", label: "Vancouver", offset: "UTC-8/-7" },
      { value: "America/Mexico_City", label: "Mexico City", offset: "UTC-6/-5" },
      { value: "America/Sao_Paulo", label: "Sao Paulo", offset: "UTC-3" },
      { value: "America/Buenos_Aires", label: "Buenos Aires", offset: "UTC-3" },
      { value: "America/Bogota", label: "Bogota", offset: "UTC-5" },
      { value: "America/Lima", label: "Lima", offset: "UTC-5" },
      { value: "America/Santiago", label: "Santiago", offset: "UTC-4/-3" },
    ],
  },
  {
    region: "Europe",
    timezones: [
      { value: "Europe/London", label: "London", offset: "UTC+0/+1" },
      { value: "Europe/Paris", label: "Paris", offset: "UTC+1/+2" },
      { value: "Europe/Berlin", label: "Berlin", offset: "UTC+1/+2" },
      { value: "Europe/Amsterdam", label: "Amsterdam", offset: "UTC+1/+2" },
      { value: "Europe/Brussels", label: "Brussels", offset: "UTC+1/+2" },
      { value: "Europe/Madrid", label: "Madrid", offset: "UTC+1/+2" },
      { value: "Europe/Rome", label: "Rome", offset: "UTC+1/+2" },
      { value: "Europe/Zurich", label: "Zurich", offset: "UTC+1/+2" },
      { value: "Europe/Vienna", label: "Vienna", offset: "UTC+1/+2" },
      { value: "Europe/Warsaw", label: "Warsaw", offset: "UTC+1/+2" },
      { value: "Europe/Stockholm", label: "Stockholm", offset: "UTC+1/+2" },
      { value: "Europe/Oslo", label: "Oslo", offset: "UTC+1/+2" },
      { value: "Europe/Copenhagen", label: "Copenhagen", offset: "UTC+1/+2" },
      { value: "Europe/Athens", label: "Athens", offset: "UTC+2/+3" },
      { value: "Europe/Helsinki", label: "Helsinki", offset: "UTC+2/+3" },
      { value: "Europe/Moscow", label: "Moscow", offset: "UTC+3" },
      { value: "Europe/Istanbul", label: "Istanbul", offset: "UTC+3" },
    ],
  },
  {
    region: "Asia",
    timezones: [
      { value: "Asia/Dubai", label: "Dubai", offset: "UTC+4" },
      { value: "Asia/Kolkata", label: "India (Kolkata)", offset: "UTC+5:30" },
      { value: "Asia/Dhaka", label: "Dhaka", offset: "UTC+6" },
      { value: "Asia/Bangkok", label: "Bangkok", offset: "UTC+7" },
      { value: "Asia/Jakarta", label: "Jakarta", offset: "UTC+7" },
      { value: "Asia/Ho_Chi_Minh", label: "Ho Chi Minh", offset: "UTC+7" },
      { value: "Asia/Singapore", label: "Singapore", offset: "UTC+8" },
      { value: "Asia/Hong_Kong", label: "Hong Kong", offset: "UTC+8" },
      { value: "Asia/Shanghai", label: "Shanghai", offset: "UTC+8" },
      { value: "Asia/Taipei", label: "Taipei", offset: "UTC+8" },
      { value: "Asia/Manila", label: "Manila", offset: "UTC+8" },
      { value: "Asia/Seoul", label: "Seoul", offset: "UTC+9" },
      { value: "Asia/Tokyo", label: "Tokyo", offset: "UTC+9" },
    ],
  },
  {
    region: "Pacific",
    timezones: [
      { value: "Australia/Perth", label: "Perth", offset: "UTC+8" },
      { value: "Australia/Adelaide", label: "Adelaide", offset: "UTC+9:30/+10:30" },
      { value: "Australia/Sydney", label: "Sydney", offset: "UTC+10/+11" },
      { value: "Australia/Melbourne", label: "Melbourne", offset: "UTC+10/+11" },
      { value: "Australia/Brisbane", label: "Brisbane", offset: "UTC+10" },
      { value: "Pacific/Auckland", label: "Auckland", offset: "UTC+12/+13" },
      { value: "Pacific/Fiji", label: "Fiji", offset: "UTC+12" },
    ],
  },
  {
    region: "Africa & Middle East",
    timezones: [
      { value: "Africa/Cairo", label: "Cairo", offset: "UTC+2" },
      { value: "Africa/Johannesburg", label: "Johannesburg", offset: "UTC+2" },
      { value: "Africa/Lagos", label: "Lagos", offset: "UTC+1" },
      { value: "Africa/Nairobi", label: "Nairobi", offset: "UTC+3" },
      { value: "Asia/Jerusalem", label: "Jerusalem", offset: "UTC+2/+3" },
      { value: "Asia/Riyadh", label: "Riyadh", offset: "UTC+3" },
    ],
  },
  {
    region: "Other",
    timezones: [{ value: "UTC", label: "UTC", offset: "UTC+0" }],
  },
];

export const ALL_TIMEZONES: TimezoneOption[] = TIMEZONE_GROUPS.flatMap(
  (group) => group.timezones
);

export function getDefaultTimezone(): string {
  if (typeof window === "undefined") {
    return "UTC";
  }
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function findTimezoneOption(value: string): TimezoneOption | undefined {
  return ALL_TIMEZONES.find((tz) => tz.value === value);
}

export function getTimezoneLabel(value: string): string {
  const option = findTimezoneOption(value);
  if (option) {
    return `${option.label} (${option.offset})`;
  }
  return value;
}
