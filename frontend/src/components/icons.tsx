import type { SVGProps } from "react";

import ArrowUpRightSource from "../assets/icons/arrow-up-right.svg?react";
import CheckSource from "../assets/icons/check.svg?react";
import ChevronLeftSource from "../assets/icons/chevron-left.svg?react";
import ChevronRightSource from "../assets/icons/chevron-right.svg?react";
import CopySource from "../assets/icons/copy.svg?react";
import MenuSource from "../assets/icons/menu.svg?react";
import PencilSource from "../assets/icons/pencil.svg?react";
import PlusSource from "../assets/icons/plus.svg?react";
import SearchSource from "../assets/icons/search.svg?react";
import TrashSource from "../assets/icons/trash-2.svg?react";
import XSource from "../assets/icons/x.svg?react";

type IconProps = SVGProps<SVGSVGElement>;

/**
 * Os SVGs da Lucide ficam em `src/assets/icons` e são importados como
 * componentes. Todos são decorativos por padrão: quem usa define o rótulo
 * acessível no elemento interativo.
 */
function createIcon(Source: typeof SearchSource) {
  return function Icon(props: IconProps) {
    return <Source aria-hidden="true" focusable="false" {...props} />;
  };
}

export const ArrowUpRightIcon = createIcon(ArrowUpRightSource);
export const CheckIcon = createIcon(CheckSource);
export const ChevronLeftIcon = createIcon(ChevronLeftSource);
export const ChevronRightIcon = createIcon(ChevronRightSource);
export const CopyIcon = createIcon(CopySource);
export const MenuIcon = createIcon(MenuSource);
export const PencilIcon = createIcon(PencilSource);
export const PlusIcon = createIcon(PlusSource);
export const SearchIcon = createIcon(SearchSource);
export const TrashIcon = createIcon(TrashSource);
export const XIcon = createIcon(XSource);
